"""Offline and live-marked tests for CrewAI, LangGraph, GenAI, and MongoDB adapters."""

import os
import sys
from types import SimpleNamespace

import pytest

from ma_co.core.models import IncidentInput, Policy, RunRecord
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine


@pytest.mark.unit
def test_crewai_mock_offline(monkeypatch):
    monkeypatch.setenv("CREWAI_MOCK", "1")
    from ma_co.adapters.crewai_incident import run_crew

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

    graph = build_graph(FixtureJudge(), FixtureRegenerator(), Policy())
    assert graph is not None


@pytest.mark.unit
def test_genai_judge_and_regenerator_offline_doubles(monkeypatch):
    class _FakeModel:
        def __init__(self, model: str) -> None:
            self.model = model

        def generate_content(self, prompt: str):
            if "strict incident-triage quality judge" in prompt:
                return SimpleNamespace(
                    text='```json\n{"score": 0.92, "critique": "Well grounded", '
                    '"missing_evidence": [], "tool_use_valid": true}\n```'
                )
            return SimpleNamespace(text="Incident ID: INC-001\nEvidence: Prometheus: 12%")

    fake_genai = SimpleNamespace(
        configure=lambda api_key: None,
        GenerativeModel=_FakeModel,
    )
    fake_google = SimpleNamespace(generativeai=fake_genai)
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.generativeai", fake_genai)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    from ma_co.adapters.genai_adapter import GenaiJudge, GenaiRegenerator

    incident = IncidentInput(
        incident_id="INC-001",
        alert="5xx spike",
        evidence=("Prometheus: 12%",),
    )
    judge = GenaiJudge()
    result = judge.evaluate(incident, "Incident ID: INC-001\nEvidence: Prometheus: 12%")
    assert result.score == 0.92
    assert result.critique == "Well grounded"

    regen = GenaiRegenerator()
    revised, cost = regen.regenerate(incident, "draft", "cite evidence")
    assert "INC-001" in revised
    assert cost == 0.001


@pytest.mark.unit
def test_mongo_run_store_offline_double(monkeypatch):
    docs: dict[str, dict] = {}

    class _FakeCol:
        def replace_one(self, flt, doc, upsert=False):
            docs[flt["_id"]] = dict(doc)

        def find_one(self, flt):
            found = docs.get(flt["_id"])
            return dict(found) if found is not None else None

    class _FakeClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def __getitem__(self, db_name: str):
            return {"runs": _FakeCol()}

    monkeypatch.setitem(sys.modules, "pymongo", SimpleNamespace(MongoClient=_FakeClient))
    from ma_co.adapters.mongo_store import MongoRunStore

    store = MongoRunStore(uri="mongodb://localhost:27017")
    record: RunRecord = ReflectionEngine(
        FixtureJudge(),
        FixtureRegenerator(),
        Policy(),
    ).run(
        IncidentInput(
            incident_id="INC-001",
            alert="5xx",
            evidence=("Prometheus: 12%",),
            proposed_action="rollback",
        ),
        "draft",
    )
    store.save(record)
    loaded = store.get(record.run_id)
    assert loaded is not None
    assert loaded.run_id == record.run_id
    assert store.get("00000000-0000-0000-0000-000000000000") is None


@pytest.mark.live
def test_genai_judge_live():
    """Requires GOOGLE_API_KEY in environment."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    from ma_co.adapters.genai_adapter import GenaiJudge

    incident = IncidentInput(
        incident_id="INC-001",
        alert="5xx spike",
        evidence=("Prometheus: 12%",),
    )
    judge = GenaiJudge()
    result = judge.evaluate(incident, "Incident ID: INC-001\nEvidence: Prometheus: 12%")
    assert 0.0 <= result.score <= 1.0
