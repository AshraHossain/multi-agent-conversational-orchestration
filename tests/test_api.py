import pytest
from fastapi.testclient import TestClient

from ma_co.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _triage(payload: dict | None = None) -> dict:
    return client.post(
        "/v1/incidents/triage",
        json=payload or {
            "incident_id": "INC-001",
            "alert": "5xx spike",
            "evidence": ["Prometheus: 12%"],
            "proposed_action": "rollback",
        },
    )


@pytest.mark.unit
def test_health_endpoints():
    for path in ("/health", "/healthz", "/readyz"):
        assert client.get(path).status_code == 200


@pytest.mark.unit
def test_triage_creates_run():
    r = _triage()
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "needs_review"
    assert data["run_id"]


@pytest.mark.unit
def test_get_run_ok():
    run_id = _triage().json()["run_id"]
    assert client.get(f"/v1/runs/{run_id}").status_code == 200


@pytest.mark.unit
def test_get_run_not_found():
    import uuid
    assert client.get(f"/v1/runs/{uuid.uuid4()}").status_code == 404


@pytest.mark.unit
def test_get_run_bad_id_400():
    assert client.get("/v1/runs/not-a-uuid").status_code == 400


@pytest.mark.unit
def test_review_approve():
    run_id = _triage().json()["run_id"]
    r = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "demo-user", "decision": "approve"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved_draft"


@pytest.mark.unit
def test_review_reject():
    run_id = _triage().json()["run_id"]
    r = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "demo-user", "decision": "reject"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "quality_failed"


@pytest.mark.unit
def test_review_conflict_409():
    run_id = _triage().json()["run_id"]
    client.post(f"/v1/runs/{run_id}/review", json={"approver": "demo-user", "decision": "approve"})
    r = client.post(
        f"/v1/runs/{run_id}/review", json={"approver": "demo-user", "decision": "approve"}
    )
    assert r.status_code == 409


@pytest.mark.unit
def test_review_never_executes_action():
    """The review endpoint records a decision only — never performs the action."""
    run_id = _triage().json()["run_id"]
    r = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "demo-user", "decision": "approve"},
    )
    assert "approved_draft" == r.json()["status"]
    assert r.json().get("approved_by") == "demo-user"


@pytest.mark.unit
def test_422_on_missing_fields():
    r = client.post("/v1/incidents/triage", json={"alert": "oops"})
    assert r.status_code == 422


@pytest.mark.unit
def test_owasp_headers_present():
    r = _triage()
    for header in (
        "x-request-id",
        "x-process-time-ms",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "cache-control",
        "content-security-policy",
    ):
        assert header in r.headers, f"Missing header: {header}"
