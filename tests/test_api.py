"""Integration tests for FastAPI security middleware, idempotency, async intake, CLI, and eval."""

import hashlib
import hmac
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ma_co import cli
from ma_co import eval as eval_mod
from ma_co.api import main as api_main
from ma_co.api.main import app, reset_rate_limiter
from ma_co.telemetry import metrics, start_span


@pytest.fixture(autouse=True)
def _clean_env_and_rate_limiter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reset_rate_limiter()
    metrics.reset()
    monkeypatch.setattr(api_main, "store", api_main.RunStore(str(tmp_path / "runs")))
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("MAX_PAYLOAD_BYTES", raising=False)
    monkeypatch.delenv("WEBHOOK_SIGNING_SECRET", raising=False)


@pytest.mark.integration
def test_health_readiness_and_metrics_probes() -> None:
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

    m_resp = client.get("/metrics")
    assert m_resp.status_code == 200
    assert "ma_co_http_requests_total" in m_resp.text
    assert "ma_co_triage_runs_total" in m_resp.text


@pytest.mark.integration
def test_api_review_never_executes_action_and_chains_audit_digest() -> None:
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
    created = response.json()
    run_id = created["run_id"]
    assert created["status"] == "needs_review"
    assert created["audit_digest"]
    assert client.get(f"/v1/runs/{run_id}").status_code == 200

    review = client.post(
        f"/v1/runs/{run_id}/review",
        json={"approver": "demo-user", "decision": "approve"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved_draft"
    assert review.json()["approved_by"] == "demo-user"
    assert review.json()["audit_digest"] != created["audit_digest"]

    # Re-reviewing a terminal run is rejected with 409 Conflict
    assert (
        client.post(
            f"/v1/runs/{run_id}/review",
            json={"approver": "demo-user", "decision": "approve"},
        ).status_code
        == 409
    )


@pytest.mark.integration
def test_idempotency_key_and_list_runs() -> None:
    client = TestClient(app)
    payload = {
        "incident_id": "INC-IDEM-1",
        "alert": "5xx spike",
        "evidence": ["Prometheus: 12%"],
        "proposed_action": "Propose rollback",
    }
    first = client.post("/v1/incidents/triage", json=payload, headers={"Idempotency-Key": "k-1"})
    assert first.status_code == 201
    run_id = first.json()["run_id"]

    replay = client.post("/v1/incidents/triage", json=payload, headers={"Idempotency-Key": "k-1"})
    assert replay.status_code == 200
    assert replay.json()["run_id"] == run_id

    conflict = client.post(
        "/v1/incidents/triage",
        json={**payload, "alert": "different alert"},
        headers={"Idempotency-Key": "k-1"},
    )
    assert conflict.status_code == 409

    listed = client.get("/v1/runs?status=needs_review&limit=10")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["runs"][0]["run_id"] == run_id


@pytest.mark.integration
def test_async_triage_intake_and_polling() -> None:
    client = TestClient(app)
    payload = {
        "incident_id": "INC-ASYNC-1",
        "alert": "Elevated latency",
        "evidence": ["Prometheus p99=900ms"],
        "proposed_action": "Review autoscale",
    }
    accepted = client.post(
        "/v1/incidents/triage/async",
        json=payload,
        headers={"Idempotency-Key": "async-k-1"},
    )
    assert accepted.status_code == 202
    run_id = accepted.json()["run_id"]
    assert accepted.json()["status"] == "pending"

    # TestClient executes BackgroundTasks before returning, so polling sees completion
    polled = client.get(f"/v1/runs/{run_id}")
    assert polled.status_code == 200
    assert polled.json()["status"] == "needs_review"

    # Replaying the same Idempotency-Key returns the existing run with 200
    replay = client.post(
        "/v1/incidents/triage/async",
        json=payload,
        headers={"Idempotency-Key": "async-k-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["run_id"] == run_id


@pytest.mark.integration
def test_webhook_hmac_signature_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    secret = "super-webhook-secret"
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", secret)

    body_dict = {
        "incident_id": "INC-HMAC-1",
        "alert": "5xx spike",
        "evidence": ["Prometheus: 12%"],
    }
    raw_body = json.dumps(body_dict).encode("utf-8")

    # Missing signature rejected
    assert (
        client.post(
            "/v1/incidents/triage", content=raw_body, headers={"Content-Type": "application/json"}
        ).status_code
        == 401
    )

    # Valid signature accepted
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + raw_body, hashlib.sha256).hexdigest()
    ok = client.post(
        "/v1/incidents/triage",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Signature-256": f"sha256={sig}",
        },
    )
    assert ok.status_code == 201


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

    bad_mime = client.post(
        "/v1/incidents/triage",
        content=b"plain text",
        headers={"Content-Type": "text/plain"},
    )
    assert bad_mime.status_code == 415

    monkeypatch.setenv("MAX_PAYLOAD_BYTES", "50")
    too_large = client.post(
        "/v1/incidents/triage",
        json={"incident_id": "INC-1", "alert": "A" * 200},
    )
    assert too_large.status_code == 413
    monkeypatch.delenv("MAX_PAYLOAD_BYTES", raising=False)

    traversal = client.post(
        "/v1/incidents/triage",
        json={"incident_id": "../etc/passwd", "alert": "probe"},
    )
    assert traversal.status_code == 400

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


@pytest.mark.unit
def test_telemetry_start_span_noop_and_otel_double(monkeypatch: pytest.MonkeyPatch) -> None:
    with start_span("noop.span", {"k": "v"}) as sp:
        sp.set_attribute("extra", 1)

    recorded: dict[str, object] = {}

    class _FakeSpan:
        def set_attribute(self, key: str, value: object) -> None:
            recorded[key] = value

    class _FakeTracer:
        @contextmanager
        def start_as_current_span(self, name: str):
            recorded["span_name"] = name
            yield _FakeSpan()

    fake_trace = SimpleNamespace(get_tracer=lambda name: _FakeTracer())
    fake_otel = SimpleNamespace(trace=fake_trace)
    monkeypatch.setitem(sys.modules, "opentelemetry", fake_otel)
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", fake_trace)

    with start_span("otel.span", {"incident_id": "INC-1"}):
        pass
    assert recorded == {"span_name": "otel.span", "incident_id": "INC-1"}


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
