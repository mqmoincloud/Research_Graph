from langchain_core.tools import tool

from app.config import LANE_NAMES, log
from app.llm import ask_with_tools


@tool(parse_docstring=True)
def technical_research(skills: list[str]) -> dict:
    """Research programming skills on GitHub.

    Call this ONLY if the job requires writing or maintaining code:
    programming languages, frameworks, databases, infrastructure. Do NOT
    call it for non-engineering roles such as HR, sales, marketing or
    operations.

    Args:
        skills: The technical skills to research.
    """
    return {"lane": "technical", "skills": skills, "role_summary": ""}


@tool(parse_docstring=True)
def soft_research(skills: list[str]) -> dict:
    """Research behavioural and people skills.

    Call this ONLY if people skills are a MAIN part of the job: hiring,
    coaching, stakeholder management, team leadership. Do NOT call it for
    hands-on engineering roles where writing code is the main work.

    Args:
        skills: The behavioural skills to research.
    """
    return {"lane": "soft", "skills": skills, "role_summary": ""}


@tool(parse_docstring=True)
def general_research(role: str, topics: list[str]) -> dict:
    """Research the company, the industry and the interview format.

    ALWAYS call this one, for every job description, whatever the role is.

    Args:
        role: One sentence describing what this role is.
        topics: Company, industry or domain topics to research.
    """
    return {"lane": "general", "skills": topics, "role_summary": role}


ALL_TOOLS = [technical_research, soft_research, general_research]

TOOL_BY_NAME = {}
for _tool in ALL_TOOLS:
    TOOL_BY_NAME[_tool.name] = _tool


ORCHESTRATOR_SYSTEM = (
    "You plan interview research for a candidate.\n"
    "\n"
    "Read the job description, decide what kind of role it is, then call "
    "EVERY tool that fits that role.\n"
    "\n"
    "Call them ALL IN ONE REPLY. Do not call one tool and stop - a plan "
    "with only one lane is an incomplete plan and will be rejected.\n"
    "\n"
    "  hands-on engineering role  ->  technical_research AND general_research\n"
    "  people-focused role        ->  soft_research AND general_research\n"
    "\n"
    "general_research is MANDATORY. Call it in every single reply, for "
    "every job description, whatever the role is.\n"
    "\n"
    "Skip only the tools that genuinely do not fit - calling a wrong tool "
    "wastes the research budget, but skipping a right one ruins the plan."
)


def log_skip(name, reason):
    log("orchestrator", "chhoda: " + str(name) + " - " + reason)


def log_plan(calls, tool_calls_log, selected_lanes):
    log("orchestrator", "LLM ne " + str(len(calls)) + " tool call kiye")

    for line in tool_calls_log:
        log("orchestrator", "   " + line)

    skipped = []
    for lane in LANE_NAMES:
        if lane not in selected_lanes:
            skipped.append(lane)

    if len(skipped) > 0:
        log("orchestrator", "   LLM ne ye NAHI chune: " + str(skipped))


def empty_plan():
    log("orchestrator", "koi kaam ka tool call nahi aaya - teeno lanes chalayenge")
    return {
        "role_summary": "",
        "requirements": [],
        "selected_lanes": LANE_NAMES,
        "tool_calls_log": [],
        "round": 0,
    }


def orchestrator(state):
    jd = state.get("jd_text", "")

    calls = ask_with_tools(ORCHESTRATOR_SYSTEM, jd, ALL_TOOLS)

    if len(calls) == 0:
        return empty_plan()

    requirements = []
    selected_lanes = []
    tool_calls_log = []
    role_summary = ""

    for call in calls:
        name = call.get("name")
        arguments = call.get("args") or {}

        chosen_tool = TOOL_BY_NAME.get(name)
        if chosen_tool is None:
            log_skip(name, "aisa koi tool hai hi nahi")
            continue

        try:
            plan = chosen_tool.invoke(arguments)
        except Exception as error:
            log_skip(name, "arguments galat the (" + type(error).__name__ + ")")
            continue

        lane = plan["lane"]
        selected_lanes.append(lane)
        tool_calls_log.append(name + " " + str(arguments))

        if plan["role_summary"] != "":
            role_summary = plan["role_summary"]

        for skill in plan["skills"]:
            requirements.append({"skill": skill, "lane": lane})

    if len(selected_lanes) == 0:
        return empty_plan()

    if role_summary == "":
        role_summary = "the role described in the job description"

    log_plan(calls, tool_calls_log, selected_lanes)

    return {
        "role_summary": role_summary,
        "requirements": requirements,
        "selected_lanes": selected_lanes,
        "tool_calls_log": tool_calls_log,
        "round": 0,
    }
