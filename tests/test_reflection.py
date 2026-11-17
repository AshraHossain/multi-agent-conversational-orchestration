import pytest
from pydantic import ValidationError

from ma_co.core.models import IncidentInput, Policy, Status
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine

_INCIDENT = IncidentInput(
    incident_id="INC-R01",
    alert="DB timeout",
    evidence=("pg_stat: 500 conns",),
    proposed_action="restart",
)

_POLICY = Policy(
    max_regenerations=3,
    min_score=0.8,
    require_human_approval=True,
    max_estimated_cost_usd=10.0,
    forbidden_tools=frozenset(),
)


def _engine(policy: Policy = _POLICY) -> ReflectionEngine:
    return ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)


@pytest.mark.unit
def test_pass_to_needs_review():
    draft = "Incident ID: INC-R01\nEvidence: pg_stat: 500 conns"
    record = _engine().run(_INCIDENT, draft)
    assert record.status == Status.NEEDS_REVIEW


@pytest.mark.unit
def test_draft_missing_evidence_triggers_regen():
    record = _engine().run(_INCIDENT, "Triage: DB timeout. Cause unconfirmed.")
    assert any(it.judge.score >= 0.8 for it in record.iterations)


@pytest.mark.unit
def test_cost_cap_stops_loop():
    from ma_co.core.models import JudgeResult

    class CostlyJudge:
        def evaluate(self, incident, draft) -> JudgeResult:
            return JudgeResult(score=0.1, critique="x", estimated_cost_usd=1.0)

    policy = _POLICY.model_copy(update={"max_estimated_cost_usd": 0.5})
    engine = ReflectionEngine(CostlyJudge(), FixtureRegenerator(), policy)
    record = engine.run(_INCIDENT, "some draft")
    assert record.status == Status.COST_EXCEEDED


@pytest.mark.unit
def test_negative_cost_raises():
    class BadRegen:
        def regenerate(self, incident, draft, critique):
            return draft + " x", -1.0

    engine = ReflectionEngine(FixtureJudge(), BadRegen(), _POLICY)
    with pytest.raises(ValueError, match="Negative cost"):
        engine.run(_INCIDENT, "bad")


@pytest.mark.unit
def test_forbidden_tool_raises():
    policy = _POLICY.model_copy(update={"forbidden_tools": frozenset({"rm"})})
    with pytest.raises(ValueError, match="Forbidden tool"):
        _engine(policy).run(_INCIDENT, "draft", used_tools={"rm"})


@pytest.mark.unit
def test_idempotent_draft_stops_loop():
    class IdentityRegen:
        def regenerate(self, incident, draft, critique):
            return draft, 0.0

    engine = ReflectionEngine(FixtureJudge(), IdentityRegen(), _POLICY)
    record = engine.run(_INCIDENT, "exact same draft")
    assert len(record.iterations) >= 1


@pytest.mark.unit
def test_no_proposed_action_gives_approved_draft():
    incident = IncidentInput(
        incident_id="INC-R02",
        alert="High CPU",
        evidence=("top: 95%",),
        proposed_action="",
    )
    draft = "Incident ID: INC-R02\nEvidence: top: 95%"
    record = _engine().run(incident, draft)
    assert record.status == Status.APPROVED_DRAFT


@pytest.mark.unit
def test_record_is_frozen():
    record = _engine().run(_INCIDENT, "draft")
    with pytest.raises((TypeError, ValidationError)):
        record.draft = "mutated"  # type: ignore[misc]


@pytest.mark.unit
def test_improvement_delta_computed():
    draft = "Incident ID: INC-R01\nEvidence: pg_stat: 500 conns"
    record = _engine().run(_INCIDENT, draft)
    assert isinstance(record.improvement_delta, float)
