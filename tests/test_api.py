from fastapi.testclient import TestClient

from ma_co.api.main import app


def test_api_review_never_executes_action():
    client = TestClient(app)
    response = client.post("/v1/incidents/triage", json={"incident_id": "INC-001", "alert": "5xx",
                        "evidence": ["Prometheus: 12%"], "proposed_action": "rollback"})
    assert response.status_code == 201
    run_id = response.json()["run_id"]
    assert response.json()["status"] == "needs_review"
    assert client.get(f"/v1/runs/{run_id}").status_code == 200
    review = client.post(f"/v1/runs/{run_id}/review", json={"approver": "demo-user", "decision": "approve"})
    assert review.status_code == 200 and review.json()["status"] == "approved_draft"
    assert client.post(f"/v1/runs/{run_id}/review", json={"approver": "demo-user", "decision": "approve"}).status_code == 409
