"""Hardened FastAPI boundary for policy-gated incident triage, streaming, and Incident Cockpit."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import (
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from ma_co.api.runtime import RuntimeBundle, build_runtime, execute_triage
from ma_co.core.models import (
    ApprovalInput,
    FollowUpInput,
    IncidentInput,
    Iteration,
    Policy,
    RunListResponse,
    RunRecord,
    Status,
    utc_now,
)
from ma_co.core.reflection import ReflectionEngine
from ma_co.core.store import RunStore, RunStoreProtocol
from ma_co.core.validation import compute_audit_digest, redact_secrets, sanitize_identifier
from ma_co.logging_config import configure_logging
from ma_co.telemetry import metrics

configure_logging()
log = logging.getLogger(__name__)

_PROBE_PATHS = frozenset({"/health", "/healthz", "/readyz", "/metrics"})
_PUBLIC_UI_PATHS = frozenset({"/cockpit"})
_DEFAULT_MAX_PAYLOAD_BYTES = 1_048_576
_DEFAULT_RATE_LIMIT_PER_MINUTE = 120
_MAX_TRACKED_CLIENTS = 1024
_WEBHOOK_MAX_SKEW_SECONDS = 300
_COCKPIT_HTML_PATH = Path(__file__).resolve().parent / "cockpit.html"

_TERMINAL_STATUSES = frozenset(
    {
        Status.APPROVED_DRAFT,
        Status.NEEDS_REVIEW,
        Status.QUALITY_FAILED,
        Status.COST_EXCEEDED,
    }
)

_rate_lock = Lock()
_rate_windows: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limiter() -> None:
    """Clear sliding-window rate limiter state (intended for test isolation)."""
    with _rate_lock:
        _rate_windows.clear()


def _extract_token(request: Request) -> str:
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return api_key.strip()
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _verify_webhook_signature(request: Request, body: bytes, secret: str) -> bool:
    timestamp = request.headers.get("X-Timestamp", "").strip()
    signature = request.headers.get("X-Signature-256", "").strip()
    if not timestamp or not signature.startswith("sha256="):
        return False
    try:
        ts_val = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts_val) > _WEBHOOK_MAX_SKEW_SECONDS:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)


def _prune_stale_rate_windows(cutoff: float) -> None:
    stale_keys = [key for key, dq in _rate_windows.items() if not dq or dq[-1] < cutoff]
    for key in stale_keys:
        _rate_windows.pop(key, None)


def _check_rate_limit(client_key: str, limit_per_minute: int) -> tuple[bool, int]:
    """Return (allowed, remaining) with bounded memory via stale-key eviction."""
    if limit_per_minute <= 0:
        return True, limit_per_minute
    now = time.monotonic()
    cutoff = now - 60.0
    with _rate_lock:
        if len(_rate_windows) > _MAX_TRACKED_CLIENTS:
            _prune_stale_rate_windows(cutoff)
        window = _rate_windows[client_key]
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= limit_per_minute:
            return False, 0
        window.append(now)
        return True, max(0, limit_per_minute - len(window))


def _attach_security_headers(
    response: Response,
    request_id: str,
    elapsed_ms: float,
    *,
    is_ui_page: bool = False,
) -> Response:
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if is_ui_page:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Module-level runtime state (synchronized via configure_runtime and compatible with tests)
runtime: RuntimeBundle = build_runtime()
store: RunStoreProtocol = runtime.store
policy: Policy = runtime.policy
engine: ReflectionEngine = runtime.engine


def configure_runtime(bundle: RuntimeBundle | None = None) -> RuntimeBundle:
    """Swap active runtime dependencies (store, policy, engine, telemetry)."""
    global runtime, store, policy, engine
    runtime = bundle or build_runtime()
    store = runtime.store
    policy = runtime.policy
    engine = runtime.engine
    return runtime


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Multi-Agent Incident Cockpit",
    version="0.3.0",
    description=(
        "Policy-gated incident triage using a bounded reflection loop, CrewAI multi-agent "
        "drafting, idempotent & async 202 intake, SSE streaming, conversational follow-ups, "
        "HMAC webhook signing, audit-digest chaining, Prometheus/OTLP metrics, and Cockpit UI."
    ),
    contact={"name": "Ashrafuzzaman Hossain", "url": "https://github.com/AshraHossain"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "incidents", "description": "Triage, stream, follow-up, list, and review runs."},
        {"name": "probes", "description": "Liveness, readiness, and Prometheus metrics."},
        {"name": "ui", "description": "Interactive Incident Cockpit operator UI."},
    ],
    lifespan=_lifespan,
)


@app.middleware("http")
async def security_and_telemetry_middleware(request: Request, call_next: Any) -> Response:
    """Enforce auth, webhook HMAC, rate limiting, MIME/size caps, metrics, and OWASP headers."""
    start = time.perf_counter()
    raw_req_id = request.headers.get("X-Request-ID", "").strip()
    request_id = raw_req_id[:64] if raw_req_id and raw_req_id.isascii() else str(uuid4())
    path = request.url.path
    is_ui = path in _PUBLIC_UI_PATHS and request.method == "GET"

    def _error_response(
        status_code: int,
        detail: str,
        extra_headers: dict[str, str] | None = None,
    ) -> Response:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        metrics.record_request(request.method, path, status_code, elapsed_ms)
        resp = JSONResponse({"detail": detail}, status_code=status_code, headers=extra_headers)
        return _attach_security_headers(resp, request_id, elapsed_ms)

    limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", str(_DEFAULT_RATE_LIMIT_PER_MINUTE)))
    remaining = limit
    if path not in _PROBE_PATHS and not is_ui:
        expected_token = os.getenv("API_AUTH_TOKEN", "").strip()
        if expected_token:
            provided = _extract_token(request)
            if not provided or not hmac.compare_digest(provided, expected_token):
                return _error_response(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

        client_host = request.client.host if request.client else "unknown"
        allowed, remaining = _check_rate_limit(client_host, limit)
        if not allowed:
            return _error_response(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Rate limit exceeded",
                extra_headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        if request.method == "POST":
            content_type = request.headers.get("content-type", "").lower()
            if not content_type.startswith("application/json"):
                return _error_response(
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    "Content-Type must be application/json",
                )

            max_bytes = int(os.getenv("MAX_PAYLOAD_BYTES", str(_DEFAULT_MAX_PAYLOAD_BYTES)))
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    if int(content_length) > max_bytes:
                        return _error_response(413, "Payload too large")
                except ValueError:
                    return _error_response(status.HTTP_400_BAD_REQUEST, "Invalid Content-Length")

            body = await request.body()
            if len(body) > max_bytes:
                return _error_response(413, "Payload too large")

            webhook_secret = os.getenv("WEBHOOK_SIGNING_SECRET", "").strip()
            if webhook_secret and not _verify_webhook_signature(request, body, webhook_secret):
                return _error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Invalid webhook signature",
                )

    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    metrics.record_request(request.method, path, response.status_code, elapsed_ms)
    log.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "elapsed_ms": round(elapsed_ms, 2),
        },
    )
    _attach_security_headers(response, request_id, elapsed_ms, is_ui_page=is_ui)
    if path not in _PROBE_PATHS and not is_ui:
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


def _sanitize_incident(incident: IncidentInput) -> IncidentInput:
    if any(sep in incident.incident_id for sep in ("/", "\\", "..")):
        raise HTTPException(status_code=400, detail="Invalid incident ID")
    try:
        safe_id = sanitize_identifier(incident.incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID") from None
    if safe_id != incident.incident_id:
        return incident.model_copy(update={"incident_id": safe_id})
    return incident


def _incident_payload_hash(incident: IncidentInput) -> str:
    return hashlib.sha256(incident.model_dump_json().encode("utf-8")).hexdigest()


def _check_idempotency(
    idempotency_key: str | None,
    payload_hash: str,
) -> RunRecord | None:
    if not idempotency_key:
        return None
    existing = store.get_idempotency(idempotency_key.strip())
    if existing is None:
        return None
    saved_hash, run_id = existing
    if saved_hash != payload_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key reused with different payload",
        )
    return store.get(run_id)


def _run_background_triage(
    run_id: str,
    incident: IncidentInput,
    use_crewai: bool,
) -> None:
    running = RunRecord(
        run_id=run_id,
        incident=incident,
        draft="Triage in progress...",
        status=Status.RUNNING,
        updated_at=utc_now(),
    )
    store.save(running)

    def _on_iter(it: Iteration) -> None:
        current = store.get(run_id)
        if current is None:
            return
        store.save(
            current.model_copy(
                update={
                    "iterations": (*current.iterations, it),
                    "draft": it.draft,
                    "updated_at": utc_now(),
                }
            )
        )

    final_record = execute_triage(
        engine,
        incident,
        telemetry=runtime.telemetry,
        use_crewai=use_crewai,
        crew_model=runtime.crew_model,
        on_iteration=_on_iter,
        run_id=run_id,
    )
    store.save(final_record)


@app.get("/health", tags=["probes"])
@app.get("/healthz", tags=["probes"])
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": app.version}


@app.get("/readyz", tags=["probes"])
def readyz() -> dict[str, str]:
    """Readiness probe verifying active run store health."""
    if not store.is_ready():
        raise HTTPException(status_code=503, detail="Run store unavailable")
    return {"status": "ready"}


@app.get("/metrics", tags=["probes"], response_class=PlainTextResponse)
def prometheus_metrics() -> PlainTextResponse:
    """Expose in-process counters and latencies in Prometheus exposition format."""
    return PlainTextResponse(
        content=metrics.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/cockpit", tags=["ui"], response_class=HTMLResponse)
def incident_cockpit() -> HTMLResponse:
    """Serve the self-contained offline Incident Cockpit web UI."""
    if not _COCKPIT_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="Incident Cockpit UI not found")
    return HTMLResponse(content=_COCKPIT_HTML_PATH.read_text(encoding="utf-8"))


@app.post(
    "/v1/incidents/triage",
    response_model=RunRecord,
    status_code=status.HTTP_201_CREATED,
    tags=["incidents"],
)
def triage(
    incident: IncidentInput,
    response: Response,
    use_crewai: Annotated[bool, Query(description="Run 3-agent CrewAI drafter")] = False,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunRecord:
    """Run bounded reflection triage synchronously and persist the immutable RunRecord."""
    safe_incident = _sanitize_incident(incident)
    payload_hash = _incident_payload_hash(safe_incident)
    replayed = _check_idempotency(idempotency_key, payload_hash)
    if replayed is not None:
        response.status_code = status.HTTP_200_OK
        return replayed

    log.info(
        "triage_started",
        extra={
            "incident_id": safe_incident.incident_id,
            "alert_preview": redact_secrets(safe_incident.alert[:120]),
        },
    )
    record = execute_triage(
        engine,
        safe_incident,
        telemetry=runtime.telemetry,
        use_crewai=use_crewai or runtime.use_crewai,
        crew_model=runtime.crew_model,
    )
    store.save(record)
    if idempotency_key:
        store.set_idempotency(idempotency_key.strip(), payload_hash, record.run_id)
    return record


@app.post(
    "/v1/incidents/triage/async",
    response_model=RunRecord,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["incidents"],
)
def triage_async(
    incident: IncidentInput,
    background_tasks: BackgroundTasks,
    response: Response,
    use_crewai: Annotated[bool, Query(description="Run 3-agent CrewAI drafter")] = False,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunRecord:
    """Accept an incident for asynchronous triage (202 Accepted); poll /v1/runs/{run_id}."""
    safe_incident = _sanitize_incident(incident)
    payload_hash = _incident_payload_hash(safe_incident)
    replayed = _check_idempotency(idempotency_key, payload_hash)
    if replayed is not None:
        response.status_code = status.HTTP_200_OK
        return replayed

    pending = RunRecord(
        incident=safe_incident,
        draft="Queued for asynchronous read-only triage...",
        status=Status.PENDING,
        updated_at=utc_now(),
    )
    pending = pending.model_copy(update={"audit_digest": compute_audit_digest(pending)})
    store.save(pending)
    if idempotency_key:
        store.set_idempotency(idempotency_key.strip(), payload_hash, pending.run_id)
    background_tasks.add_task(
        _run_background_triage,
        pending.run_id,
        safe_incident,
        use_crewai or runtime.use_crewai,
    )
    return pending


@app.get("/v1/runs", response_model=RunListResponse, tags=["incidents"])
def list_runs(
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    incident_id: Annotated[str | None, Query(max_length=80)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RunListResponse:
    """List persisted triage runs with optional status/incident_id filters and pagination."""
    items, total = store.list_runs(
        status=status_filter,
        incident_id=incident_id,
        limit=limit,
        offset=offset,
    )
    items_tuple = tuple(items)
    return RunListResponse(
        items=items_tuple,
        runs=items_tuple,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/v1/runs/{run_id}", response_model=RunRecord, tags=["incidents"])
def get_run(run_id: str) -> RunRecord:
    """Retrieve a persisted triage run by UUID."""
    try:
        UUID(run_id)
        record = store.get(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID") from None
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@app.get("/v1/runs/{run_id}/stream", tags=["incidents"])
async def stream_run(run_id: str) -> StreamingResponse:
    """Stream Server-Sent Events (SSE) for a run's iterations until terminal status."""
    initial = get_run(run_id)

    async def _event_generator() -> AsyncIterator[str]:
        sent_iterations = 0
        current = initial
        for _ in range(100):
            while sent_iterations < len(current.iterations):
                it = current.iterations[sent_iterations]
                payload = json.dumps(
                    {
                        "run_id": current.run_id,
                        "iteration": it.number,
                        "score": it.judge.score,
                        "critique": it.judge.critique,
                        "missing_evidence": list(it.judge.missing_evidence),
                        "draft": it.draft,
                    }
                )
                yield f"event: iteration\ndata: {payload}\n\n"
                sent_iterations += 1

            if current.status in _TERMINAL_STATUSES:
                yield f"event: complete\ndata: {current.model_dump_json()}\n\n"
                return

            await asyncio.sleep(0.05)
            refreshed = store.get(run_id)
            if refreshed is None:
                return
            current = refreshed

        yield f"event: timeout\ndata: {current.model_dump_json()}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@app.post(
    "/v1/runs/{run_id}/follow-up",
    response_model=RunRecord,
    status_code=status.HTTP_201_CREATED,
    tags=["incidents"],
)
def follow_up(
    run_id: str,
    payload: FollowUpInput,
    use_crewai: Annotated[bool, Query(description="Run 3-agent CrewAI drafter")] = False,
) -> RunRecord:
    """Create an immutable child triage run incorporating new operator evidence or context."""
    parent = get_run(run_id)
    merged_evidence = tuple(dict.fromkeys((*parent.incident.evidence, *payload.evidence)))[:20]
    next_action = (
        payload.proposed_action
        if payload.proposed_action is not None
        else parent.incident.proposed_action
    )
    updated_incident = parent.incident.model_copy(
        update={
            "evidence": merged_evidence,
            "proposed_action": next_action,
        }
    )
    child = execute_triage(
        engine,
        updated_incident,
        telemetry=runtime.telemetry,
        use_crewai=use_crewai or runtime.use_crewai,
        crew_model=runtime.crew_model,
        parent_run_id=parent.run_id,
        follow_up_note=payload.note,
    )
    store.save(child)
    return child


@app.post("/v1/runs/{run_id}/review", response_model=RunRecord, tags=["incidents"])
def review(run_id: str, request: ApprovalInput) -> RunRecord:
    """Record a human approval or rejection decision with chained audit digest (no execution)."""
    record = get_run(run_id)
    if record.status != Status.NEEDS_REVIEW:
        raise HTTPException(status_code=409, detail="No action pending review")
    now = utc_now()
    updated = record.model_copy(
        update={
            "approved_by": request.approver if request.decision == "approve" else None,
            "reviewed_by": request.approver,
            "review_decision": request.decision,
            "review_note": request.note,
            "reviewed_at": now,
            "status": (
                Status.APPROVED_DRAFT if request.decision == "approve" else Status.QUALITY_FAILED
            ),
            "updated_at": now,
        }
    )
    chained = updated.model_copy(
        update={"audit_digest": compute_audit_digest(updated, previous_digest=record.audit_digest)}
    )
    store.save(chained)
    return chained


__all__ = ["RunStore", "app", "configure_runtime", "reset_rate_limiter"]
