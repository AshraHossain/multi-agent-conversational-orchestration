"""Graph owns the bounded loop; action execution is deliberately outside the graph."""
from typing import TypedDict

from ma_co.core.models import IncidentInput, Policy
from ma_co.core.reflection import Judge, Regenerator


class State(TypedDict, total=False):
    incident: dict
    draft: str
    score: float
    critique: str
    missing_evidence: list[str]
    tool_use_valid: bool
    regenerations: int
    cost: float
    status: str
    history: list[dict]


def build_graph(judge: Judge, regenerator: Regenerator, policy: Policy):
    from langgraph.graph import END, START, StateGraph

    def evaluate(state: State) -> dict:
        incident = IncidentInput.model_validate(state["incident"])
        result = judge.evaluate(incident, state["draft"])
        history = state.get("history", [])[-3:] + [{"score": result.score, "critique": result.critique[:500]}]
        return {"score": result.score, "critique": result.critique,
                "missing_evidence": result.missing_evidence, "tool_use_valid": result.tool_use_valid,
                "cost": state.get("cost", 0) + result.estimated_cost_usd, "history": history}

    def route(state: State) -> str:
        if state.get("cost", 0) > policy.max_estimated_cost_usd:
            return "stop"
        if (state["score"] >= policy.min_score and state["tool_use_valid"]
                and not state["missing_evidence"]):
            return "stop"
        if state.get("regenerations", 0) >= policy.max_regenerations:
            return "stop"
        return "regenerate"

    def regenerate(state: State) -> dict:
        candidate, cost = regenerator.regenerate(IncidentInput.model_validate(state["incident"]),
                                                  state["draft"], state["critique"])
        if cost < 0:
            raise ValueError("Negative cost")
        return {"draft": candidate, "cost": state.get("cost", 0) + cost,
                "regenerations": state.get("regenerations", 0) + 1}

    def finish(state: State) -> dict:
        passing = (state.get("cost", 0) <= policy.max_estimated_cost_usd
                   and state["score"] >= policy.min_score and state["tool_use_valid"]
                   and not state["missing_evidence"])
        incident = IncidentInput.model_validate(state["incident"])
        return {"status": ("needs_review" if passing and incident.proposed_action
                            and policy.require_human_approval else "approved_draft" if passing
                            else "quality_failed")}

    graph = StateGraph(State)
    graph.add_node("evaluate", evaluate)
    graph.add_node("regenerate", regenerate)
    graph.add_node("finish", finish)
    graph.add_edge(START, "evaluate")
    graph.add_conditional_edges("evaluate", route, {"regenerate": "regenerate", "stop": "finish"})
    graph.add_edge("regenerate", "evaluate")
    graph.add_edge("finish", END)
    return graph.compile()
