from ma_co.adapters.langgraph_reflection import build_graph
from ma_co.core.models import IncidentInput, Policy, Status
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine


def incident(action: str = "") -> IncidentInput:
    return IncidentInput(incident_id="INC-001", alert="Elevated 5xx",
                         evidence=["Prometheus: 12%"], proposed_action=action)


def test_reflects_and_requests_review():
    result = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy()).run(incident("rollback"), "draft")
    assert result.status == Status.NEEDS_REVIEW
    assert len(result.iterations) == 2 and result.improvement_delta > 0


def test_bounded_failure():
    result = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy(max_regenerations=0)).run(incident(), "draft")
    assert result.status == Status.QUALITY_FAILED


def test_graph_route():
    graph = build_graph(FixtureJudge(), FixtureRegenerator(), Policy(max_regenerations=1))
    result = graph.invoke({"incident": incident("rollback").model_dump(), "draft": "draft"})
    assert result["status"] == "needs_review" and result["regenerations"] == 1
