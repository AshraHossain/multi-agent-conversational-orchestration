import json
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from ma_co.core.models import ApprovalInput, IncidentInput, Policy, RunRecord, Status, utc_now
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore

app = FastAPI(title="Multi-Agent Incident Cockpit", version="0.1.0")
store = RunStore()
policy = Policy.model_validate(json.loads(Path("policies/default.json").read_text(encoding="utf-8")))
engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/incidents/triage", response_model=RunRecord, status_code=status.HTTP_201_CREATED)
def triage(incident: IncidentInput) -> RunRecord:
    # Fixture-only API: opt-in live CrewAI is a separate CLI, not a request-time fallback.
    draft = f"Incident {incident.incident_id}: {incident.alert}. Root cause unconfirmed."
    record = engine.run(incident, draft)
    store.save(record)
    return record


@app.get("/v1/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: str) -> RunRecord:
    try:
        UUID(run_id)
        record = store.get(run_id)
    except ValueError:
        raise HTTPException(400, "Invalid run ID") from None
    if record is None:
        raise HTTPException(404, "Run not found")
    return record


@app.post("/v1/runs/{run_id}/review", response_model=RunRecord)
def review(run_id: str, request: ApprovalInput) -> RunRecord:
    record = get_run(run_id)
    if record.status != Status.NEEDS_REVIEW:
        raise HTTPException(409, "No action pending review")
    record.approved_by = request.approver if request.decision == "approve" else None
    record.status = Status.APPROVED_DRAFT if request.decision == "approve" else Status.QUALITY_FAILED
    record.updated_at = utc_now()
    store.save(record)
    # This endpoint records a demo decision. It NEVER performs the proposed action.
    return record
