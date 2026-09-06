from app.config import LANE_NAMES, MAX_ROUNDS, log
from app.llm import ask_json


def build_review_prompt(req_lines, ev_lines):

    return (
        "Decide whether enough material has been collected to write an "
        "interview preparation document.\n"
        "\n"
        "Requirements to cover:\n" + "\n".join(req_lines) + "\n"
        "\n"
        "Material collected so far:\n" + "\n".join(ev_lines) + "\n"
        "\n"
        "For each lane, list what is still missing.\n"
        "If a lane has enough material, give an empty list.\n"
        "At most 2 items per lane. Keep each item short and searchable.\n"
        "\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        '  "missing_by_lane": {\n'
        '    "technical": ["FastAPI testing"],\n'
        '    "soft": [],\n'
        '    "general": []\n'
        "  }\n"
        "}"
    )


def clean_missing(raw_missing, selected_lanes):

    missing = {}

    for lane in LANE_NAMES:
        if lane not in selected_lanes:
            missing[lane] = []
            continue

        gaps = raw_missing.get(lane, [])
        if not isinstance(gaps, list):
            gaps = []
        missing[lane] = gaps

    return missing


def lanes_with_gaps(missing):

    lanes = []
    for lane in LANE_NAMES:
        if len(missing[lane]) > 0:
            lanes.append(lane)
    return lanes


def review(state):

    round_number = state.get("round", 0)
    requirements = state.get("requirements", [])
    evidence = state.get("evidence", [])
    next_round = round_number + 1

    selected_lanes = state.get("selected_lanes", [])
    if len(selected_lanes) == 0:
        selected_lanes = LANE_NAMES

    if state.get("always_missing"):
        raw_missing = {
            "technical": ["deeper code examples"],
            "soft": [],
            "general": ["interview format"],
        }
    else:
        req_lines = []
        for req in requirements:
            req_lines.append("- " + req["lane"] + " : " + req["skill"])

        ev_lines = []
        for ev in evidence:
            ev_lines.append("- " + ev["lane"] + " : " + ev["skill"] + " : " + ev["title"])

        prompt = build_review_prompt(req_lines, ev_lines)

        answer = ask_json(prompt, ["missing_by_lane"])
        raw_missing = answer["missing_by_lane"]

    missing = clean_missing(raw_missing, selected_lanes)
    lanes_to_rerun = lanes_with_gaps(missing)

    exhausted = len(lanes_to_rerun) > 0 and next_round >= MAX_ROUNDS

    log("review", str(len(evidence)) + " evidence | gaps: " + str(lanes_to_rerun)
        + " | round " + str(round_number) + " -> " + str(next_round))

    return {
        "missing_by_lane": missing,
        "lanes_to_rerun": lanes_to_rerun,
        "round": next_round,
        "exhausted": exhausted,
    }
