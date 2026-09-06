import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import LANE_NAMES, LANE_TO_NODE, MAX_ROUNDS, log
from app.nodes.compose import compose
from app.nodes.orchestrator import orchestrator
from app.nodes.research import general_research, soft_research, tech_research
from app.nodes.review import review


class PrepState(TypedDict, total=False):
    jd_text: str

    role_summary: str
    requirements: list
    selected_lanes: list

    evidence: Annotated[list, operator.add]

    tool_calls_log: list

    missing_by_lane: dict
    lanes_to_rerun: list
    round: int
    exhausted: bool

    prep_document: str

    always_missing: bool


def choose_lanes(state):
    selected = state.get("selected_lanes", [])

    node_names = []
    skipped = []
    for lane in LANE_NAMES:
        if lane in selected:
            node_names.append(LANE_TO_NODE[lane])
        else:
            skipped.append(lane)

    if len(node_names) == 0:
        log("fan-out", "kuch nahi chuna gaya - teeno chala rahe hain")
        return list(LANE_TO_NODE.values())

    if len(skipped) > 0:
        log("fan-out", "LLM ne chune: " + str(node_names) + "  |  SKIP: " + str(skipped))
    else:
        log("fan-out", "LLM ne teeno chune: " + str(node_names))

    return node_names


def decide_next_step(state):
    lanes = state.get("lanes_to_rerun", [])
    round_number = state.get("round", 0)

    if len(lanes) == 0:
        log("router", "koi kami nahi -> compose")
        return "compose"

    if round_number >= MAX_ROUNDS:
        log("router", "budget khatam -> compose")
        return "compose"

    node_names = []
    for lane in lanes:
        node_names.append(LANE_TO_NODE[lane])

    log("router", "kami hai " + str(lanes) + " -> dobara chalao " + str(node_names))
    return node_names


def build_graph():
    builder = StateGraph(PrepState)

    builder.add_node("orchestrator", orchestrator)
    builder.add_node("tech_research", tech_research)
    builder.add_node("soft_research", soft_research)
    builder.add_node("general_research", general_research)
    builder.add_node("review", review)
    builder.add_node("compose", compose)

    builder.add_edge(START, "orchestrator")

    builder.add_conditional_edges(
        "orchestrator",
        choose_lanes,
        ["tech_research", "soft_research", "general_research"],
    )

    builder.add_edge("tech_research", "review")
    builder.add_edge("soft_research", "review")
    builder.add_edge("general_research", "review")

    builder.add_conditional_edges(
        "review",
        decide_next_step,
        ["tech_research", "soft_research", "general_research", "compose"],
    )

    builder.add_edge("compose", END)

    return builder.compile()
