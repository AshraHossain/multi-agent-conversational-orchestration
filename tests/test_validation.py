from ma_co.core.models import IncidentInput, Policy, Status
from ma_co.core.reflection import (
    FixtureJudge,
    FixtureRegenerator,
    ReflectionEngine,
)
from ma_co.core.validation import validate_incident_draft


def sample_incident() -> IncidentInput:
    return IncidentInput(
        incident_id="INC-001",
        alert="Elevated 5xx",
        evidence=["Prometheus: 12% at 10:05 UTC"],
        proposed_action="Review rollback",
    )


def test_rejects_changed_incident_id():
    defects = validate_incident_draft(
        sample_incident(),
        "## Incident ID: P2-High-5xx-Errors\nEvidence: Prometheus: 12%",
    )
    assert any("incident ID" in defect for defect in defects)


def test_rejects_evidence_contradiction():
    defects = validate_incident_draft(
        sample_incident(),
        "Incident ID: INC-001\n"
        "No fixture evidence was available.\n"
        "Evidence: Prometheus: 12% at 10:05 UTC",
    )
    assert any("denies" in defect for defect in defects)


def test_evidence_marker_cannot_override_defects():
    record = ReflectionEngine(
        FixtureJudge(),
        FixtureRegenerator(),
        Policy(max_regenerations=1),
    ).run(
        sample_incident(),
        "Incident ID: WRONG\nNo fixture evidence was available.\n"
        "Evidence: Prometheus: 12%",
    )

    assert record.status == Status.QUALITY_FAILED
    assert record.iterations[-1].judge.score == 0.0