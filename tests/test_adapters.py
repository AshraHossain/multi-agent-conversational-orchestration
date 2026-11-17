import os

import pytest


@pytest.mark.unit
def test_crewai_mock_offline(monkeypatch):
    monkeypatch.setenv("CREWAI_MOCK", "1")
    from ma_co.adapters.crewai_incident import run_crew
    from ma_co.core.models import IncidentInput

    incident = IncidentInput(
        incident_id="INC-001",
        alert="5xx spike",
        evidence=("Prometheus: 12%",),
        proposed_action="rollback",
    )
    draft, critique = run_crew(incident, "mock-model")
    assert "INC-001" in draft
    assert critique


@pytest.mark.unit
def test_langgraph_graph_builds():
    from ma_co.adapters.langgraph_reflection import build_graph
    from ma_co.core.models import Policy
    from ma_co.core.reflection import FixtureJudge, FixtureRegenerator

    graph = build_graph(FixtureJudge(), FixtureRegenerator(), Policy())
    assert graph is not None


@pytest.mark.live
def test_genai_judge_live():
    """Requires GOOGLE_API_KEY in environment."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    from ma_co.adapters.genai_adapter import GenaiJudge
    from ma_co.core.models import IncidentInput

    incident = IncidentInput(
        incident_id="INC-001",
        alert="5xx spike",
        evidence=("Prometheus: 12%",),
    )
    judge = GenaiJudge()
    result = judge.evaluate(incident, "Incident ID: INC-001\nEvidence: Prometheus: 12%")
    assert 0.0 <= result.score <= 1.0
