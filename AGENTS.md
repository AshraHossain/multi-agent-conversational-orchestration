# AGENTS.md — Multi-Agent Conversational Orchestration (`ma_co`)

Portable instructions for **Antigravity (Gemini)**, **Claude Code**, and other coding agents.

## What This Project Is
An enterprise incident-response orchestration service (`src/ma_co/`) that combines a read-only three-agent **CrewAI** crew (`Triager -> Investigator -> Safety Reviewer`), a bounded **LangGraph** reflection state machine, a deterministic **SRAF-style policy & quality gate engine**, and a hardened **FastAPI** `/v1/incidents/triage` API.

## Verified Commands
```bash
make setup                                           # uv sync --group dev
make check                                           # lint + test (>=80% cov) + eval harness
make lint                                            # uv run ruff check .
make test                                            # uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80
make eval                                            # uv run python -m ma_co.eval
make dev                                             # uv run uvicorn ma_co.api.main:app --reload
uv run python -m ma_co.cli                           # run offline CLI triage flow
CREWAI_MOCK=1 uv run python -m ma_co.cli --live-crewai  # run 3-agent CrewAI adapter with offline mock
```

## Module Layout
```text
src/ma_co/
  core/
    models.py          # Frozen Pydantic DTOs (Policy, IncidentInput, JudgeResult, Iteration, RunRecord, ApprovalInput)
    validation.py      # Pure deterministic draft validators, ID sanitizer, and <untrusted_context> framing
    reflection.py      # Judge/Regenerator protocols, Fixture implementations, and immutable ReflectionEngine
    store.py           # Thread-safe atomic JSON RunStore with path-traversal protection
  adapters/
    crewai_incident.py      # 3-agent sequential CrewAI adapter (supports CREWAI_MOCK=1 offline fallback)
    langgraph_reflection.py # Bounded LangGraph reflection state machine (with pure fallback if langgraph absent)
    genai_adapter.py        # google-generativeai live Judge + Regenerator (requires GOOGLE_API_KEY)
    mongo_store.py          # MongoDB-backed RunStore implementing same save/get interface (requires MONGO_URI)
  api/
    main.py            # FastAPI endpoints (/health, /healthz, /readyz, /v1/incidents/triage, /v1/runs/{id}, /review)
                       # + Auth (401), Rate-Limit (429), Size (413), MIME (415), and OWASP security middleware
  tools/
    fixtures.py        # Read-only telemetry lookup (Prometheus, GitHub, Kubernetes) + source allowlist
  cli.py               # Offline-default CLI entrypoint with opt-in --live-crewai flag
  eval.py              # Reproducible evaluation & latency benchmark runner (-> evaluation/eval_report.json)
```

## Repo-Specific Invariants
1. **Read-Only Triage**: Agents never execute live rollbacks, deployments, or emails; all actions are proposed and gated by `Policy` and human review (`/v1/runs/{run_id}/review` only records decisions).
2. **Fixture-Default Execution**: Default runs use `FixtureJudge` and `FixtureRegenerator` (and `CREWAI_MOCK=1` when testing CrewAI) with zero live network calls unless `--live-crewai` is explicitly invoked with `BYNARA_API_KEY`.
3. **Deterministic Core vs. AI Layering**: Quality-gate math, cost caps, retry bounds, ID matching, contradiction checks, and `<untrusted_context>` sanitization live in pure Python functions in `ma_co/core/` — never in prompts.
4. **Immutability**: All Pydantic schemas use `ConfigDict(frozen=True)`; state transitions return new instances via `model_copy(update=...)`.
5. **Defense-in-Depth Security**: Enforce timing-safe `hmac.compare_digest` auth (`API_AUTH_TOKEN`), sliding-window rate limiting (`RATE_LIMIT_PER_MINUTE`), payload byte caps (`MAX_PAYLOAD_BYTES`), `application/json` MIME checks, path-safe IDs, and OWASP headers.
