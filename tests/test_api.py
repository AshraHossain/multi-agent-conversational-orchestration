"""Integration tests for FastAPI security middleware, endpoints, CLI, and eval harness."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ma_co import cli
from ma_co import eval as eval_mod
from ma_co.api import main as api_main
from ma_co.api.main import app, reset_rate_limiter


@pytest.fixture(autouse=True)
def _clean_env_and_rate_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_rate_limiter()
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("MAX_PAYLOAD_BYTES", raising=False)


@pytest.mark.integration
def test_health_and_readiness_probes() -> None:
    client = TestClient(app)
    for path in ("/health", "/healthz", "/readyz"):
        resp = client.get(path)
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "no-referrer"
        assert resp.headers["Cache-Control"] == "no-store"
        assert "default-src 'none'" in resp.headers["Content-Security-Policy"]


@pytest.mark.integration
def test_api_review_never_executes_action() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-001",
            "alert": "5xx",
            "evidence": ["Prometheus: 12%"],
            "proposed_action": "rollback",
        },
    )
    assert response.status_code == 201
    run_id = response.json()["run_id"]
    assert response.json()["status"] == "needs_review"
    assert client.get(f"/v1/runs/{run_id}").status_code == 200

    review = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "demo-user", "decision": "approve"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved_draft"
    assert review.json()["approved_by"] == "demo-user"

    # Re-reviewing a terminal run is rejected with 409 Conflict
    assert (
        client.post(
            f"/v1/runs/{run_id}/review",
            json={"approver": "demo-user", "decision": "approve"},
        ).status_code
        == 409
    )


@pytest.mark.integration
def test_api_review_reject_and_run_lookup_errors() -> None:
    client = TestClient(app)
    created = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-002",
            "alert": "latency spike",
            "evidence": ["Prometheus: p99=900ms"],
            "proposed_action": "scale up",
        },
    )
    run_id = created.json()["run_id"]
    rejected = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "sec-lead", "decision": "reject"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "quality_failed"
    assert rejected.json()["approved_by"] is None

    assert client.get("/v1/runs/not-a-uuid").status_code == 400
    assert client.get(f"/v1/runs/{uuid4()}").status_code == 404


@pytest.mark.integration
def test_api_security_auth_rate_limit_size_mime_and_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = TestClient(app)

    # 1. Timing-safe Auth (401) while probes remain open
    monkeypatch.setenv("API_AUTH_TOKEN", "secret-token-123")
    assert client.get("/healthz").status_code == 200
    assert (
        client.post(
            "/v1/incidents/triage",
            json={"incident_id": "INC-1", "alert": "x"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/v1/incidents/triage",
            json={"incident_id": "INC-1", "alert": "x"},
            headers={"Authorization": "Bearer wrong-token"},
        ).status_code
        == 401
    )
    ok_auth = client.post(
        "/v1/incidents/triage",
        json={"incident_id": "INC-1", "alert": "x", "evidence": ["e1"]},
        headers={"X-API-Key": "secret-token-123"},
    )
    assert ok_auth.status_code == 201
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)

    # 2. MIME allowlist (415)
    bad_mime = client.post(
        "/v1/incidents/triage",
        content=b"plain text",
        headers={"Content-Type": "text/plain"},
    )
    assert bad_mime.status_code == 415

    # 3. Payload size cap (413)
    monkeypatch.setenv("MAX_PAYLOAD_BYTES", "50")
    too_large = client.post(
        "/v1/incidents/triage",
        json={"incident_id": "INC-1", "alert": "A" * 200},
    )
    assert too_large.status_code == 413
    monkeypatch.delenv("MAX_PAYLOAD_BYTES", raising=False)

    # 4. Path traversal in incident_id (400)
    traversal = client.post(
        "/v1/incidents/triage",
        json={"incident_id": "../etc/passwd", "alert": "probe"},
    )
    assert traversal.status_code == 400

    # 5. Sliding-window rate limiting (429)
    reset_rate_limiter()
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    assert client.get(f"/v1/runs/{uuid4()}").status_code == 404
    assert client.get(f"/v1/runs/{uuid4()}").status_code == 404
    limited = client.get(f"/v1/runs/{uuid4()}")
    assert limited.status_code == 429
    assert limited.headers.get("Retry-After") == "60"


@pytest.mark.integration
def test_readyz_returns_503_when_store_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing_dir = tmp_path / "does_not_exist"
    monkeypatch.setattr(api_main.store, "directory", missing_dir)
    client = TestClient(app)
    assert client.get("/readyz").status_code == 503


@pytest.mark.integration
def test_cli_offline_and_mock_crewai(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([]) == 0
    out_default = capsys.readouterr().out
    assert '"status": "needs_review"' in out_default

    monkeypatch.setenv("CREWAI_MOCK", "1")
    assert cli.main(["--live-crewai"]) == 0
    out_crew = capsys.readouterr().out
    assert "crew_reviewer_feedback" in out_crew


@pytest.mark.integration
def test_eval_runner_and_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    scorecard = eval_mod.run_eval(output_path=tmp_path / "evaluation" / "eval_report.json")
    assert scorecard["policy_accuracy"] == 1.0
    assert scorecard["evidence_grounding_rate"] == 1.0
    assert scorecard["guardrail_pass_rate"] == 1.0

    eval_mod.main([])
    stdout = capsys.readouterr().out
    assert "Policy Accuracy" in stdout
    assert (tmp_path / "evaluation" / "eval_report.json").exists()
