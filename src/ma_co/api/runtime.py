"""Runtime wiring factory connecting FastAPI edge to configured stores, LLMs, and crews."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ma_co.core.models import IncidentInput, Iteration, Policy, RunRecord
from ma_co.core.reflection import (
    FixtureJudge,
    FixtureRegenerator,
    Judge,
    ReflectionEngine,
    Regenerator,
)
from ma_co.core.store import RunStore, RunStoreProtocol
from ma_co.observability import metrics, trace_span
from ma_co.tools.providers import TelemetryProvider, get_telemetry_provider

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class RuntimeBundle:
    """Immutable dependency container assembled from environment configuration."""

    store: RunStoreProtocol
    policy: Policy
    engine: ReflectionEngine
    telemetry: TelemetryProvider
    use_crewai: bool = False
    crew_model: str = "deepseek-v4-flash"
    use_langgraph: bool = False


def load_policy(policy_path: str | None = None) -> Policy:
    """Load policy JSON from configured path, CWD, or package repository fallback."""
    candidate_str = policy_path or os.getenv("POLICY_PATH") or "policies/default.json"
    candidate = Path(candidate_str)
    if not candidate.exists():
        fallback = _REPO_ROOT / "policies" / "default.json"
        if fallback.exists():
            candidate = fallback
        else:
            return Policy()
    return Policy.model_validate(json.loads(candidate.read_text(encoding="utf-8")))


def _build_store() -> RunStoreProtocol:
    backend = os.getenv("MA_CO_STORE_BACKEND", "").strip().lower()
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if backend == "mongo" or (mongo_uri and backend != "local"):
        from ma_co.adapters.mongo_store import MongoRunStore

        return MongoRunStore(
            uri=mongo_uri or None,
            db_name=os.getenv("MONGO_DB_NAME", "ma_co"),
            collection=os.getenv("MONGO_COLLECTION", "runs"),
        )
    return RunStore(directory=os.getenv("RUN_STORE_DIR", "artifacts/runs"))


def _build_judge_and_regenerator() -> tuple[Judge, Regenerator]:
    provider = os.getenv("MA_CO_LLM_PROVIDER", "fixture").strip().lower()
    if provider == "genai":
        from ma_co.adapters.genai_adapter import GenaiJudge, GenaiRegenerator

        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
        return GenaiJudge(model=model), GenaiRegenerator(model=model)
    return FixtureJudge(), FixtureRegenerator()


def build_runtime() -> RuntimeBundle:
    """Build a RuntimeBundle honoring env toggles while defaulting 100% offline."""
    policy = load_policy()
    store = _build_store()
    judge, regenerator = _build_judge_and_regenerator()
    engine = ReflectionEngine(judge, regenerator, policy)
    telemetry = get_telemetry_provider()
    use_crewai = os.getenv("MA_CO_USE_CREWAI", "0").strip() == "1"
    crew_model = os.getenv("NARA_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash"
    use_langgraph = os.getenv("MA_CO_USE_LANGGRAPH", "0").strip() == "1"
    return RuntimeBundle(
        store=store,
        policy=policy,
        engine=engine,
        telemetry=telemetry,
        use_crewai=use_crewai,
        crew_model=crew_model,
        use_langgraph=use_langgraph,
    )


def execute_triage(
    engine: ReflectionEngine,
    incident: IncidentInput,
    *,
    telemetry: TelemetryProvider | None = None,
    use_crewai: bool = False,
    crew_model: str = "deepseek-v4-flash",
    on_iteration: Callable[[Iteration], None] | None = None,
    run_id: str | None = None,
    parent_run_id: str | None = None,
    follow_up_note: str = "",
) -> RunRecord:
    """Execute read-only drafting + bounded reflection and emit observability telemetry."""
    with trace_span(
        "triage.execute",
        {
            "incident_id": incident.incident_id,
            "use_crewai": use_crewai,
            "has_parent": parent_run_id is not None,
        },
    ):
        reviewer_feedback = ""
        if use_crewai:
            from ma_co.adapters.crewai_incident import run_crew

            draft, reviewer_feedback = run_crew(incident, crew_model, provider=telemetry)
        else:
            draft = f"Incident {incident.incident_id}: {incident.alert}. Root cause unconfirmed."
            if follow_up_note:
                draft += f"\nFollow-up context: {follow_up_note}"

        record = engine.run(
            incident,
            draft,
            on_iteration=on_iteration,
            run_id=run_id,
            parent_run_id=parent_run_id,
            follow_up_note=follow_up_note,
            reviewer_feedback=reviewer_feedback,
        )
        veto_count = sum(
            1
            for it in record.iterations
            if "Deterministic validation failures:" in it.judge.critique
        )
        metrics.record_triage_run(
            status=record.status.value,
            iterations=len(record.iterations),
            estimated_cost_usd=record.estimated_cost_usd,
            veto_count=veto_count,
        )
        return record
