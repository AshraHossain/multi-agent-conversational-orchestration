"""Graph owns the bounded loop; action execution is deliberately outside the graph."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypedDict

from ma_co.core.models import IncidentInput, Policy
from ma_co.core.reflection import Judge, Regenerator, apply_deterministic_veto


class State(TypedDict, total=False):
    incident: dict[str, Any]
    draft: str
    score: float
    critique: str
    missing_evidence: list[str]
    tool_use_valid: bool
    regenerations: int
    cost: float
    status: str
    history: list[dict[str, Any]]


class InvokableGraph(Protocol):
    """Minimal protocol shared by compiled LangGraph StateGraph and pure fallback."""

    def invoke(self, initial_state: State) -> dict[str, Any]: ...


class _FallbackGraph:
    """Pure-Python fallback when langgraph is not installed."""

    def __init__(
        self,
        evaluate: Callable[[State], dict[str, Any]],
        route: Callable[[State], str],
        regenerate: Callable[[State], dict[str, Any]],
        finish: Callable[[State], dict[str, Any]],
    ) -> None:
        self._evaluate = evaluate
        self._route = route
        self._regenerate = regenerate
        self._finish = finish

    def invoke(self, initial_state: State) -> dict[str, Any]:
        state: dict[str, Any] = dict(initial_state)
        while True:
            state.update(self._evaluate(state))  # type: ignore[arg-type]
            if self._route(state) == "stop":  # type: ignore[arg-type]
                state.update(self._finish(state))  # type: ignore[arg-type]
                return state
            state.update(self._regenerate(state))  # type: ignore[arg-type]


def build_graph(judge: Judge, regenerator: Regenerator, policy: Policy) -> Any:
    """Build a bounded reflection state machine using LangGraph or pure fallback."""

    def evaluate(state: State) -> dict[str, Any]:
        incident = IncidentInput.model_validate(state["incident"])
        raw_result = judge.evaluate(incident, state["draft"])
        result = apply_deterministic_veto(incident, state["draft"], raw_result)
        history = [
            *state.get("history", [])[-3:],
            {"score": result.score, "critique": result.critique[:500]},
        ]
        return {
            "score": result.score,
            "critique": result.critique,
            "missing_evidence": list(result.missing_evidence),
            "tool_use_valid": result.tool_use_valid,
            "cost": state.get("cost", 0.0) + result.estimated_cost_usd,
            "history": history,
        }

    def route(state: State) -> str:
        if state.get("cost", 0.0) > policy.max_estimated_cost_usd:
            return "stop"
        if (
            state["score"] >= policy.min_score
            and state["tool_use_valid"]
            and not state["missing_evidence"]
        ):
            return "stop"
        if state.get("regenerations", 0) >= policy.max_regenerations:
            return "stop"
        return "regenerate"

    def regenerate(state: State) -> dict[str, Any]:
        candidate, cost = regenerator.regenerate(
            IncidentInput.model_validate(state["incident"]),
            state["draft"],
            state["critique"],
        )
        if cost < 0:
            raise ValueError("Negative cost")
        return {
            "draft": candidate,
            "cost": state.get("cost", 0.0) + cost,
            "regenerations": state.get("regenerations", 0) + 1,
        }

    def finish(state: State) -> dict[str, Any]:
        cost = state.get("cost", 0.0)
        if cost > policy.max_estimated_cost_usd:
            return {"status": "cost_exceeded"}
        passing = (
            state["score"] >= policy.min_score
            and state["tool_use_valid"]
            and not state["missing_evidence"]
        )
        incident = IncidentInput.model_validate(state["incident"])
        if passing and incident.proposed_action and policy.require_human_approval:
            status = "needs_review"
        elif passing:
            status = "approved_draft"
        else:
            status = "quality_failed"
        return {"status": status}

    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError:
        return _FallbackGraph(evaluate, route, regenerate, finish)

    graph = StateGraph(State)
    graph.add_node("evaluate", evaluate)
    graph.add_node("regenerate", regenerate)
    graph.add_node("finish", finish)
    graph.add_edge(START, "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        route,
        {"regenerate": "regenerate", "stop": "finish"},
    )
    graph.add_edge("regenerate", "evaluate")
    graph.add_edge("finish", END)
    return graph.compile()
