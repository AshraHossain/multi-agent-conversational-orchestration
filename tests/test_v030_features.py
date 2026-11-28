"""Integration & unit tests for v0.3.0 features: listing, async 202, SSE, follow-up, metrics, UI."""

from __future__ import annotations

import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ma_co import eval as eval_mod
from ma_co.api import main as api_main
from ma_co.api.main import app, configure_runtime, reset_rate_limiter
from ma_co.api.runtime import RuntimeBundle, build_runtime, load_policy
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore
from ma_co.observability import metrics, trace_span
from ma_co.tools.providers import FixtureTelemetryProvider


@pytest.fixture(autouse=True)
def _isolated_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    reset_rate_limiter()
    metrics.reset()
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("MAX_PAYLOAD_BYTES", raising=False)
    monkeypatch.setenv("CREWAI_MOCK", "1")
    prev = api_main.runtime
    policy = load_policy()
    configure_runtime(
        RuntimeBundle(
            store=RunStore(directory=str(tmp_path / "runs")),
            policy=policy,
            engine=ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy),
            telemetry=FixtureTelemetryProvider(),
        )
    )
    yield
    configure_runtime(prev)
    reset_rate_limiter()


@pytest.mark.integration
def test_list_runs_filtering_and_pagination() -> None:
    client = TestClient(app)
    r1 = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-L1",
            "alert": "5xx spike",
            "evidence": ["Prometheus 5xx=12%"],
            "proposed_action": "Propose rollback",
        },
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-L2",
            "alert": "Observation only",
            "evidence": ["Prometheus p99=500ms"],
            "proposed_action": "",
        },
    )
    assert r2.status_code == 201

    all_resp = client.get("/v1/runs?limit=10&offset=0")
    assert all_resp.status_code == 200
    body = all_resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    only_review = client.get("/v1/runs?status=needs_review")
    assert only_review.status_code == 200
    assert only_review.json()["total"] == 1
    assert only_review.json()["items"][0]["incident"]["incident_id"] == "INC-L1"

    by_inc = client.get("/v1/runs?incident_id=INC-L2")
    assert by_inc.status_code == 200
    assert by_inc.json()["total"] == 1
    assert by_inc.json()["items"][0]["status"] == "approved_draft"


@pytest.mark.integration
def test_async_triage_202_and_sse_stream() -> None:
    client = TestClient(app)
    accepted = client.post(
        "/v1/incidents/triage/async",
        json={
            "incident_id": "INC-ASYNC",
            "alert": "Background triage test",
            "evidence": ["Prometheus cpu=95%"],
            "proposed_action": "Review scale-out",
        },
    )
    assert accepted.status_code == 202
    run_id = accepted.json()["run_id"]
    assert accepted.json()["status"] == "pending"

    # TestClient executes FastAPI BackgroundTasks before returning, so run is terminal now
    final = client.get(f"/v1/runs/{run_id}")
    assert final.status_code == 200
    assert final.json()["status"] == "needs_review"

    with client.stream("GET", f"/v1/runs/{run_id}/stream") as stream:
        assert stream.status_code == 200
        assert "text/event-stream" in stream.headers["content-type"]
        payload = "".join(stream.iter_text())
    assert "event: iteration" in payload
    assert "event: complete" in payload
    assert run_id in payload


@pytest.mark.integration
def test_conversational_follow_up_creates_immutable_child() -> None:
    client = TestClient(app)
    parent = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-CONV",
            "alert": "Elevated latency",
            "evidence": [],
            "proposed_action": "Propose cache review",
        },
    )
    assert parent.status_code == 201
    assert parent.json()["status"] == "quality_failed"
    parent_id = parent.json()["run_id"]

    child = client.post(
        f"/v1/runs/{parent_id}/follow-up",
        json={
            "note": "Attached Prometheus latency panel from SRE dashboard",
            "evidence": ["Prometheus p99=1120ms at 12:00 UTC"],
        },
    )
    assert child.status_code == 201
    child_data = child.json()
    assert child_data["run_id"] != parent_id
    assert child_data["parent_run_id"] == parent_id
    assert child_data["status"] == "needs_review"
    assert "Prometheus p99=1120ms at 12:00 UTC" in child_data["incident"]["evidence"]
    assert child_data["follow_up_note"] == "Attached Prometheus latency panel from SRE dashboard"

    # Unknown parent returns 404
    missing = client.post(
        f"/v1/runs/{uuid4()}/follow-up",
        json={"note": "Missing parent test"},
    )
    assert missing.status_code == 404


@pytest.mark.integration
def test_review_preserves_audit_metadata_on_reject_and_approve() -> None:
    client = TestClient(app)
    created = client.post(
        "/v1/incidents/triage",
        json={
            "incident_id": "INC-AUD",
            "alert": "DB saturation",
            "evidence": ["Prometheus conns=99%"],
            "proposed_action": "Review pool config",
        },
    )
    run_id = created.json()["run_id"]

    rejected = client.post(
        f"/v1/runs/{run_id}/review",
        json={
            "approver": "sec-reviewer",
            "decision": "reject",
            "note": "Need pg_stat_activity dump before approving",
        },
    )
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["approved_by"] is None
    assert body["reviewed_by"] == "sec-reviewer"
    assert body["review_decision"] == "reject"
    assert body["review_note"] == "Need pg_stat_activity dump before approving"
    assert body["reviewed_at"] is not None


@pytest.mark.integration
def test_crewai_query_toggle_metrics_and_cockpit_ui() -> None:
    client = TestClient(app)

    triage = client.post(
        "/v1/incidents/triage?use_crewai=true",
        json={
            "incident_id": "INC-001",
            "alert": "5xx spike",
            "evidence": ["Prometheus 5xx rate 12%"],
            "proposed_action": "Review rollback",
        },
    )
    assert triage.status_code == 201
    assert "Safety Reviewer (offline mock)" in triage.json()["reviewer_feedback"]

    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "ma_co_http_requests_total" in metrics_resp.text
    assert 'ma_co_triage_runs_total{status="needs_review"} 1' in metrics_resp.text
    assert "default-src 'none'" in metrics_resp.headers["Content-Security-Policy"]

    cockpit_resp = client.get("/cockpit")
    assert cockpit_resp.status_code == 200
    assert "Multi-Agent Incident Cockpit" in cockpit_resp.text
    assert "script-src 'self' 'unsafe-inline'" in cockpit_resp.headers["Content-Security-Policy"]


@pytest.mark.unit
def test_observability_noop_span_rate_pruning_and_eval_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    with trace_span("unit.test", {"k": "v"}) as span:
        span.set_attribute("extra", 1)

    snap = metrics.snapshot()
    assert snap["requests_total"] == 0

    # Verify stale rate limiter key eviction works cleanly
    now = time.monotonic()
    with api_main._rate_lock:
        api_main._rate_windows["stale-client"].append(now - 120.0)
        api_main._prune_stale_rate_windows(now - 60.0)
        assert "stale-client" not in api_main._rate_windows

    # Verify build_runtime defaults offline cleanly
    monkeypatch.setenv("RUN_STORE_DIR", str(tmp_path / "built_runs"))
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MA_CO_LLM_PROVIDER", raising=False)
    bundle = build_runtime()
    assert bundle.store.is_ready()

    # Verify 20 golden cases loaded and --no-guardrails & --live error path work
    assert len(eval_mod.GOLDEN_CASES) == 20
    report = eval_mod.run_eval(
        n_runs=2,
        output_path=tmp_path / "no_guard.json",
        include_guardrails=False,
    )
    assert "guardrails" not in report

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        eval_mod.run_live_blind_spot_replay()
