"""Unit and integration tests for ReflectionEngine, LangGraph, CrewAI mock, and RunStore."""

from pathlib import Path
from uuid import uuid4

import pytest

from ma_co.adapters.crewai_incident import run_crew
from ma_co.adapters.langgraph_reflection import _FallbackGraph, build_graph
from ma_co.core.models import IncidentInput, JudgeResult, Policy, Status
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore


def incident(action: str = "") -> IncidentInput:
    return IncidentInput(
        incident_id="INC-001",
        alert="Elevated 5xx",
        evidence=("Prometheus: 12%",),
        proposed_action=action,
    )


class _CostlyJudge:
    def evaluate(self, incident: IncidentInput, draft: str) -> JudgeResult:
        return JudgeResult(
            score=0.5,
            critique="Needs work",
            missing_evidence=("more logs",),
            estimated_cost_usd=0.06,
        )


class _NegativeCostRegen:
    def regenerate(self, incident: IncidentInput, draft: str, critique: str) -> tuple[str, float]:
        return draft + " revised", -0.01


class _CostlyRegen:
    def regenerate(self, incident: IncidentInput, draft: str, critique: str) -> tuple[str, float]:
        return draft + " revised", 0.2


class _NoOpRegen:
    def regenerate(self, incident: IncidentInput, draft: str, critique: str) -> tuple[str, float]:
        return draft, 0.0


@pytest.mark.unit
def test_reflects_and_requests_review() -> None:
    result = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy()).run(
        incident("rollback"),
        "draft",
    )
    assert result.status == Status.NEEDS_REVIEW
    assert len(result.iterations) == 2
    assert result.improvement_delta > 0


@pytest.mark.unit
def test_reflects_and_approves_without_proposed_action() -> None:
    result = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy()).run(
        incident(""),
        "draft",
    )
    assert result.status == Status.APPROVED_DRAFT


@pytest.mark.unit
def test_bounded_failure() -> None:
    result = ReflectionEngine(
        FixtureJudge(),
        FixtureRegenerator(),
        Policy(max_regenerations=0),
    ).run(incident(), "draft")
    assert result.status == Status.QUALITY_FAILED


@pytest.mark.unit
def test_reflection_rejects_forbidden_tools_and_negative_cost() -> None:
    engine = ReflectionEngine(
        FixtureJudge(),
        _NegativeCostRegen(),
        Policy(forbidden_tools=frozenset({"shell"})),
    )
    with pytest.raises(ValueError, match="Forbidden tool"):
        engine.run(incident(), "draft", used_tools={"shell"})

    with pytest.raises(ValueError, match="Negative cost"):
        engine.run(incident(), "draft")


@pytest.mark.unit
def test_reflection_stops_on_cost_exceeded_and_noop_regen() -> None:
    cost_judge_result = ReflectionEngine(
        _CostlyJudge(),
        FixtureRegenerator(),
        Policy(max_estimated_cost_usd=0.05),
    ).run(incident(), "Incident ID: INC-001 draft")
    assert cost_judge_result.status == Status.COST_EXCEEDED

    cost_regen_result = ReflectionEngine(
        FixtureJudge(),
        _CostlyRegen(),
        Policy(max_estimated_cost_usd=0.1),
    ).run(incident(), "Incident ID: INC-001 draft")
    assert cost_regen_result.status == Status.COST_EXCEEDED

    noop_result = ReflectionEngine(
        FixtureJudge(),
        _NoOpRegen(),
        Policy(max_regenerations=2),
    ).run(incident(), "Incident ID: INC-001 draft")
    assert noop_result.status == Status.QUALITY_FAILED
    assert len(noop_result.iterations) == 1


@pytest.mark.integration
def test_graph_route_all_outcomes() -> None:
    graph = build_graph(FixtureJudge(), FixtureRegenerator(), Policy(max_regenerations=1))
    result = graph.invoke({"incident": incident("rollback").model_dump(), "draft": "draft"})
    assert result["status"] == "needs_review"
    assert result["regenerations"] == 1

    approved_graph = build_graph(
        FixtureJudge(),
        FixtureRegenerator(),
        Policy(max_regenerations=1, require_human_approval=False),
    )
    approved = approved_graph.invoke(
        {"incident": incident("rollback").model_dump(), "draft": "draft"}
    )
    assert approved["status"] == "approved_draft"

    failed_graph = build_graph(FixtureJudge(), FixtureRegenerator(), Policy(max_regenerations=0))
    failed = failed_graph.invoke({"incident": incident("").model_dump(), "draft": "draft"})
    assert failed["status"] == "quality_failed"

    cost_graph = build_graph(
        _CostlyJudge(),
        FixtureRegenerator(),
        Policy(max_estimated_cost_usd=0.05),
    )
    cost_res = cost_graph.invoke(
        {"incident": incident("").model_dump(), "draft": "Incident ID: INC-001"}
    )
    assert cost_res["status"] == "cost_exceeded"


@pytest.mark.unit
def test_fallback_graph_runs_without_langgraph() -> None:
    def _eval(state):
        return {"score": 0.9, "tool_use_valid": True, "missing_evidence": [], "cost": 0.0}

    def _route(state):
        return "stop"

    def _regen(state):
        return {}

    def _finish(state):
        return {"status": "approved_draft"}

    fg = _FallbackGraph(_eval, _route, _regen, _finish)
    out = fg.invoke({"incident": incident().model_dump(), "draft": "Incident ID: INC-001"})
    assert out["status"] == "approved_draft"


@pytest.mark.unit
def test_run_store_persistence_and_path_safety(tmp_path: Path) -> None:
    store = RunStore(str(tmp_path))
    record = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy()).run(
        incident("rollback"),
        "draft",
    )
    store.save(record)
    loaded = store.get(record.run_id)
    assert loaded is not None
    assert loaded.run_id == record.run_id
    assert store.get(str(uuid4())) is None

    with pytest.raises(ValueError):
        store.get("../../etc/passwd")


@pytest.mark.unit
def test_crewai_adapter_mock_and_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CREWAI_MOCK", "1")
    draft, critique = run_crew(incident("rollback"), "deepseek-v4-flash")
    assert "INC-001" in draft
    assert "offline mock" in critique

    monkeypatch.delenv("CREWAI_MOCK", raising=False)
    monkeypatch.delenv("BYNARA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="BYNARA_API_KEY"):
        run_crew(incident("rollback"), "deepseek-v4-flash")
