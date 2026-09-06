from app.config import EVIDENCE_PER_LANE, LANE_NAMES, MAX_GITHUB_REPOS, log
from app.llm import ask_text

SECTION_NAMES = [
    "Role snapshot",
    "Must-have skills",
    "Prep plan",
    "Likely interview questions",
]


def has_material(skill, evidence):
    needle = skill.lower()

    for ev in evidence:
        found = ev["skill"].lower()
        if needle in found or found in needle:
            return True

    return False


def build_requirement_lines(requirements, evidence):
    lines = []

    for req in requirements:
        line = "- " + req["lane"] + " : " + req["skill"]

        if not has_material(req["skill"], evidence):
            line = line + "   (NO MATERIAL FOUND)"

        lines.append(line)

    return lines


def build_evidence_lines(evidence):

    lines = []
    seen_urls = []
    lane_counts = {}

    for ev in evidence:
        lane = ev["lane"]
        url = ev["url"]

        if url in seen_urls:
            continue

        if lane_counts.get(lane, 0) >= EVIDENCE_PER_LANE:
            continue

        seen_urls.append(url)
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        lines.append("- [" + lane + "] " + ev["title"] + " -- " + url)

    return lines


def build_budget_line(state):

    if not state.get("exhausted"):
        return ""

    missing = state.get("missing_by_lane", {})

    all_gaps = []
    for lane in LANE_NAMES:
        for gap in missing.get(lane, []):
            all_gaps.append(gap)

    return ("\n\nAt the end of the document, state plainly that the research "
            "budget ran out and these topics could not be covered fully: "
            + ", ".join(all_gaps))


def find_github_repos(evidence):

    github_only = []
    for ev in evidence:
        if ev["source"] == "github":
            github_only.append(ev)

    repos = []
    seen_urls = []
    skills_done = []

    for ev in github_only:
        if len(repos) >= MAX_GITHUB_REPOS:
            break
        if ev["skill"] in skills_done:
            continue
        if ev["url"] in seen_urls:
            continue

        skills_done.append(ev["skill"])
        seen_urls.append(ev["url"])
        repos.append(ev)

    for ev in github_only:
        if len(repos) >= MAX_GITHUB_REPOS:
            break
        if ev["url"] in seen_urls:
            continue

        seen_urls.append(ev["url"])
        repos.append(ev)

    return repos


def build_github_section(repos):

    heading = "\n\n## GitHub repos found in research\n\n"

    if len(repos) == 0:
        return heading + "_No GitHub repositories were found for this role._\n"

    lines = []
    for repo in repos:
        line = "- **" + repo["title"] + "** - " + repo["url"]

        if repo["snippet"] != "":
            line = line + "\n  " + repo["snippet"]

        lines.append(line)

    return heading + "\n\n".join(lines) + "\n"


def build_prompt(role_summary, req_lines, ev_lines, budget_line):
    section_lines = []
    number = 1
    for name in SECTION_NAMES:
        section_lines.append(str(number) + ". " + name)
        number = number + 1

    return (
        "Write an interview preparation document in Markdown.\n"
        "\n"
        "Role: " + role_summary + "\n"
        "\n"
        "Requirements:\n" + "\n".join(req_lines) + "\n"
        "\n"
        "Research material:\n" + "\n".join(ev_lines) + "\n"
        "\n"
        "Use exactly these sections, in this order:\n"
        + "\n".join(section_lines) + "\n"
        "\n"
        "Rules:\n"
        "- Base everything on the research material above. Do not invent links.\n"
        "- A requirement marked (NO MATERIAL FOUND) has no research behind it.\n"
        "  Do NOT write advice for it. List it once and say plainly that the\n"
        "  research did not turn anything up for it.\n"
        "- Include a link where it genuinely helps.\n"
        "- Keep it short and practical."
        + budget_line
    )


def build_fallback_document(role_summary, requirements, evidence):

    lines = [
        "# Prep plan",
        "",
        "> **Note:** the AI writer returned an empty answer every time, so this",
        "> document was assembled automatically from the research results.",
        "> It contains no advice - only what the research actually found.",
        "",
        "## Role",
        "",
        role_summary,
        "",
        "## Requirements",
    ]

    for lane in LANE_NAMES:
        lane_requirements = []
        for req in requirements:
            if req["lane"] == lane:
                lane_requirements.append(req)

        if len(lane_requirements) == 0:
            continue

        lines.append("")
        lines.append("### " + lane)

        for req in lane_requirements:
            line = "- " + req["skill"]
            if not has_material(req["skill"], evidence):
                line = line + "  _(no material found)_"
            lines.append(line)

    lines.append("")
    lines.append("## Research material")

    for lane in LANE_NAMES:
        lane_lines = []
        seen_urls = []

        for ev in evidence:
            if ev["lane"] != lane:
                continue
            if ev["url"] in seen_urls:
                continue

            seen_urls.append(ev["url"])
            lane_lines.append("- [" + ev["title"] + "](" + ev["url"] + ")")

        if len(lane_lines) == 0:
            continue

        lines.append("")
        lines.append("### " + lane)
        lines.extend(lane_lines)

    return "\n".join(lines)


def compose(state):

    role_summary = state.get("role_summary", "")
    requirements = state.get("requirements", [])
    evidence = state.get("evidence", [])

    req_lines = build_requirement_lines(requirements, evidence)
    ev_lines = build_evidence_lines(evidence)
    budget_line = build_budget_line(state)

    prompt = build_prompt(role_summary, req_lines, ev_lines, budget_line)

    try:
        document = ask_text(prompt)
        used_fallback = False
    except Exception as error:
        log("compose", "LLM fail: " + str(error))
        log("compose", "fallback document bana rahe hain (research se, bina LLM ke)")
        document = build_fallback_document(role_summary, requirements, evidence)
        used_fallback = True

    repos = find_github_repos(evidence)
    document = document + build_github_section(repos)

    covered = 0
    for req in requirements:
        if has_material(req["skill"], evidence):
            covered = covered + 1

    kind = "LLM"
    if used_fallback:
        kind = "FALLBACK"

    log("compose", kind + " | " + str(len(ev_lines)) + "/" + str(len(evidence))
        + " evidence prompt mein | " + str(covered) + "/" + str(len(requirements))
        + " requirements ka material mila | " + str(len(repos))
        + " github repos | document " + str(len(document)) + " chars")

    return {"prep_document": document}
