"""Hardened FastAPI boundary for policy-gated incident triage."""

import hmac
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from ma_co.core.models import (
    ApprovalInput,
    IncidentInput,
    Policy,
    RunRecord,
    Status,
    utc_now,
)
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore
from ma_co.core.validation import sanitize_identifier

_PROBE_PATHS = frozenset({"/health", "/healthz", "/readyz"})
_DEFAULT_MAX_PAYLOAD_BYTES = 1_048_576
_DEFAULT_RATE_LIMIT_PER_MINUTE = 120

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


def _check_rate_limit(client_key: str, limit_per_minute: int) -> bool:
    if limit_per_minute <= 0:
        return True
    now = time.monotonic()
    cutoff = now - 60.0
    with _rate_lock:
        window = _rate_windows[client_key]
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= limit_per_minute:
            return False
        window.append(now)
        return True


def _attach_security_headers(response: Response, request_id: str, elapsed_ms: float) -> Response:
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


app = FastAPI(title="Multi-Agent Incident Cockpit", version="0.2.0")
store = RunStore()
policy = Policy.model_validate(
    json.loads(Path("policies/default.json").read_text(encoding="utf-8"))
)
engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)


@app.middleware("http")
async def security_and_telemetry_middleware(request: Request, call_next) -> Response:
    """Enforce auth, rate limiting, MIME/size caps, and OWASP security headers."""
    start = time.perf_counter()
    raw_req_id = request.headers.get("X-Request-ID", "").strip()
    request_id = raw_req_id[:64] if raw_req_id and raw_req_id.isascii() else str(uuid4())

    def _error_response(
        status_code: int,
        detail: str,
        extra_headers: dict[str, str] | None = None,
    ) -> Response:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        resp = JSONResponse({"detail": detail}, status_code=status_code, headers=extra_headers)
        return _attach_security_headers(resp, request_id, elapsed_ms)

    path = request.url.path
    if path not in _PROBE_PATHS:
        expected_token = os.getenv("API_AUTH_TOKEN", "").strip()
        if expected_token:
            provided = _extract_token(request)
            if not provided or not hmac.compare_digest(provided, expected_token):
                return _error_response(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

        limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", str(_DEFAULT_RATE_LIMIT_PER_MINUTE)))
        client_host = request.client.host if request.client else "unknown"
        if not _check_rate_limit(client_host, limit):
            return _error_response(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Rate limit exceeded",
                extra_headers={"Retry-After": "60"},
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

    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return _attach_security_headers(response, request_id, elapsed_ms)


@app.get("/health")
@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness probe verifying local store directory accessibility."""
    if not store.directory.exists():
        raise HTTPException(status_code=503, detail="Run store unavailable")
    return {"status": "ready"}


@app.post("/v1/incidents/triage", response_model=RunRecord, status_code=status.HTTP_201_CREATED)
def triage(incident: IncidentInput) -> RunRecord:
    """Run bounded offline reflection triage and persist the immutable RunRecord."""
    if any(sep in incident.incident_id for sep in ("/", "\\", "..")):
        raise HTTPException(status_code=400, detail="Invalid incident ID")
    try:
        safe_id = sanitize_identifier(incident.incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID") from None
    if safe_id != incident.incident_id:
        incident = incident.model_copy(update={"incident_id": safe_id})

    draft = f"Incident {incident.incident_id}: {incident.alert}. Root cause unconfirmed."
    record = engine.run(incident, draft)
    store.save(record)
    return record


@app.get("/v1/runs/{run_id}", response_model=RunRecord)
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


@app.post("/v1/runs/{run_id}/review", response_model=RunRecord)
def review(run_id: str, request: ApprovalInput) -> RunRecord:
    """Record a human approval or rejection decision without executing external actions."""
    record = get_run(run_id)
    if record.status != Status.NEEDS_REVIEW:
        raise HTTPException(status_code=409, detail="No action pending review")
    updated = record.model_copy(
        update={
            "approved_by": request.approver if request.decision == "approve" else None,
            "status": (
                Status.APPROVED_DRAFT
                if request.decision == "approve"
                else Status.QUALITY_FAILED
            ),
            "updated_at": utc_now(),
        }
    )
    store.save(updated)
    return updated
