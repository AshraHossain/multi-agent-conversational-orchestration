import hmac
import json
import os
import time
import uuid
from collections import deque
from pathlib import Path
from threading import Lock
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from ma_co.core.models import ApprovalInput, IncidentInput, Policy, RunRecord, Status, utc_now
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore
from ma_co.core.validation import sanitize_identifier

# ---------------------------------------------------------------------------
# App & singletons
# ---------------------------------------------------------------------------
app = FastAPI(title="Multi-Agent Incident Cockpit", version="0.1.0")
store = RunStore()
policy = Policy.model_validate(
    json.loads(Path("policies/default.json").read_text(encoding="utf-8"))
)
engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
_API_AUTH_TOKEN: str | None = os.getenv("API_AUTH_TOKEN")
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
_MAX_PAYLOAD = int(os.getenv("MAX_PAYLOAD_BYTES", str(64 * 1024)))  # 64 KB

# ---------------------------------------------------------------------------
# Sliding-window rate limiter (per-process, per-IP)
# ---------------------------------------------------------------------------
_rate_windows: dict[str, deque[float]] = {}
_rate_lock = Lock()

_OPEN_PATHS = {"/health", "/healthz", "/readyz"}


def _check_rate_limit(client_ip: str) -> bool:
    now = time.monotonic()
    window = 60.0
    with _rate_lock:
        q = _rate_windows.setdefault(client_ip, deque())
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= _RATE_LIMIT:
            return False
        q.append(now)
        return True


# ---------------------------------------------------------------------------
# Middleware: auth, rate-limit, MIME, size, OWASP headers
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    # Probe paths bypass auth and rate-limit
    if request.url.path not in _OPEN_PATHS:
        # Timing-safe API key auth
        if _API_AUTH_TOKEN:
            key = request.headers.get("x-api-key", "")
            if not hmac.compare_digest(key.encode(), _API_AUTH_TOKEN.encode()):
                return JSONResponse(
                    {"detail": "Unauthorized"},
                    status_code=401,
                    headers={"X-Request-ID": request_id},
                )

        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if not _check_rate_limit(client_ip):
            return JSONResponse(
                {"detail": "Too many requests"},
                status_code=429,
                headers={"Retry-After": "60", "X-Request-ID": request_id},
            )

        # MIME type check for mutation endpoints
        if request.method in ("POST", "PUT", "PATCH"):
            ct = request.headers.get("content-type", "")
            if not ct.startswith("application/json"):
                return JSONResponse(
                    {"detail": "Unsupported Media Type"},
                    status_code=415,
                    headers={"X-Request-ID": request_id},
                )

        # Payload size cap
        cl = request.headers.get("content-length")
        if cl and int(cl) > _MAX_PAYLOAD:
            return JSONResponse(
                {"detail": "Payload too large"},
                status_code=413,
                headers={"X-Request-ID": request_id},
            )

    response: Response = await call_next(request)

    # OWASP security headers
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


# ---------------------------------------------------------------------------
# Probe endpoints (bypass auth)
# ---------------------------------------------------------------------------
@app.get("/health")
@app.get("/healthz")
@app.get("/readyz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Business endpoints
# ---------------------------------------------------------------------------
@app.post("/v1/incidents/triage", response_model=RunRecord, status_code=status.HTTP_201_CREATED)
def triage(incident: IncidentInput) -> RunRecord:
    draft = f"Incident {incident.incident_id}: {incident.alert}. Root cause unconfirmed."
    record = engine.run(incident, draft)
    store.save(record)
    return record


@app.get("/v1/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: str) -> RunRecord:
    safe_id = sanitize_identifier(run_id)
    try:
        UUID(safe_id)
    except ValueError:
        raise HTTPException(400, "Invalid run ID") from None
    record = store.get(safe_id)
    if record is None:
        raise HTTPException(404, "Run not found")
    return record


@app.post("/v1/runs/{run_id}/review", response_model=RunRecord)
def review(run_id: str, request: ApprovalInput) -> RunRecord:
    record = get_run(run_id)
    if record.status != Status.NEEDS_REVIEW:
        raise HTTPException(409, "No action pending review")
    new_status = Status.APPROVED_DRAFT if request.decision == "approve" else Status.QUALITY_FAILED
    updated = record.model_copy(
        update={
            "approved_by": request.approver if request.decision == "approve" else None,
            "status": new_status,
            "updated_at": utc_now(),
        }
    )
    store.save(updated)
    # This endpoint records a demo decision. It NEVER performs the proposed action.
    return updated
