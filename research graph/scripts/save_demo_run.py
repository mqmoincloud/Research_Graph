"""Run the graph on a demo JD and save the result, so it can be shown later.

    uv run python -m scripts.save_demo_run              # every JD in demo_jds/
    uv run python -m scripts.save_demo_run jd_backend   # just that one

Nothing stores a run: POST /api/run returns the result and that is the end of
it. Demoing the app therefore meant sitting through a real 1-3 minute run, with
the LLM having to behave on the day. This writes one real run per JD to
demo_runs/<name>.json instead, and app/routers/demo.py serves those files back.

The saved documents ARE real graph output, not something written by hand - the
only difference is when they were produced. Re-run this after changing a JD or
a node, otherwise the demo keeps showing the old answer.
"""

import json
import sys

from app.config import DEMO_JDS_FOLDER, DEMO_RUNS_FOLDER
from app.database import now
from app.graph import build_graph

# Windows terminals default to cp1252, and the documents contain characters it
# cannot print. Without this the run finishes and the summary line crashes.
sys.stdout.reconfigure(encoding="utf-8")


def first_line(jd_text):
    """The JDs start with the job title, and that makes a good button label."""
    for line in jd_text.splitlines():
        if line.strip():
            return line.strip()

    return "Untitled role"


def save_one(graph, jd_path):
    name = jd_path.stem
    jd_text = jd_path.read_text(encoding="utf-8").strip()

    print()
    print("=" * 72)
    print("Running:", name, " (this takes 1-3 minutes)")
    print("=" * 72)

    result = graph.invoke({"jd_text": jd_text})

    saved = {
        "name": name,
        "label": first_line(jd_text),
        "jd_file": jd_path.name,
        "saved_at": now().isoformat(timespec="seconds"),
        "result": result,
    }

    DEMO_RUNS_FOLDER.mkdir(exist_ok=True)
    out_path = DEMO_RUNS_FOLDER / (name + ".json")

    # default=str is a safety net. Everything in the state is a plain string,
    # list or dict today; if a node ever puts something else in there, this
    # writes a readable value instead of blowing up after the whole run.
    #
    # The newline argument keeps the file LF-only. Windows would otherwise
    # write CRLF, and a re-run would show every line as changed even when
    # the document itself is identical.
    out_path.write_text(
        json.dumps(saved, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
        newline="\n",
    )

    print()
    print("saved      :", out_path.name)
    print("evidence   :", len(result.get("evidence", [])))
    print("document   :", len(result.get("prep_document", "")), "characters")

    return out_path


def main():
    wanted = sys.argv[1:]

    jd_paths = sorted(DEMO_JDS_FOLDER.glob("*.txt"))

    if wanted:
        jd_paths = [path for path in jd_paths if path.stem in wanted]

        missing = set(wanted) - {path.stem for path in jd_paths}
        if missing:
            print("Not in demo_jds/:", ", ".join(sorted(missing)))
            return

    if not jd_paths:
        print("No JDs found in", DEMO_JDS_FOLDER)
        return

    graph = build_graph()

    for jd_path in jd_paths:
        save_one(graph, jd_path)

    print()
    print("Done -", len(jd_paths), "saved into demo_runs/")


if __name__ == "__main__":
    main()
