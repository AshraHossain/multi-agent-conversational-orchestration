# AGENTS.md — Multi-Agent Conversational Orchestration (`ma_co`)

Portable instructions for **Antigravity (Gemini)**, **Claude Code**, and other coding agents.

## What This Project Is
An enterprise incident-response orchestration service (`src/ma_co/`) that combines framework-free frozen `contracts/`, a pure deterministic `core/` policy & reflection engine, a read-only three-agent **CrewAI** crew (`Triager -> Investigator -> Safety Reviewer`), a bounded **LangGraph** state machine, a hardened **FastAPI** API, and a 3-tier evaluation harness.

## Verified Commands
```bash
make setup                                           # uv sync --group dev
make check                                           # ruff check/format + mypy + pytest (branch cov >=80%) + 3-tier eval
make lint                                            # uv run ruff check . && uv run ruff format --check .
make typecheck                                       # uv run mypy src/ma_co
make test                                            # uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80
make eval                                            # uv run python -m ma_co.eval --guardrails --verifier-matrix
make dev                                             # uv run uvicorn ma_co.api.main:app --reload
uv run python -m ma_co.cli                           # run offline CLI triage flow
CREWAI_MOCK=1 uv run python -m ma_co.cli --live-crewai  # run 3-agent CrewAI adapter with offline mock
```

## Module Layout
```text
src/ma_co/
  contracts/           # Frozen Pydantic DTOs (Status, Policy, IncidentInput, JudgeResult, Iteration, RunRecord, ApprovalInput)
  core/                # Pure deterministic validators, <untrusted_context> framing, ReflectionEngine, atomic RunStore
  adapters/            # CrewAI (CREWAI_MOCK=1), LangGraph (+ fallback), Gemini (GenaiJudge/Regenerator), MongoRunStore
  api/main.py          # FastAPI routes (/health, /healthz, /readyz, /v1/incidents/triage, /v1/runs/{id}, /review) + OWASP middleware
  tools/fixtures.py    # Read-only telemetry lookup (Prometheus, GitHub, Kubernetes)
  cli.py & eval.py     # Offline-default CLI & 3-tier eval harness (--guardrails, --verifier-matrix, --repeat N)
```

## Governance & Repo-Specific Invariants
- **Planning**: Follow [PLANNING.md](PLANNING.md) (GSD → Superpowers → Ruflo), track phases in [PLAN.md](PLAN.md) & [TASK.md](TASK.md), and record trade-offs in `docs/adr/`. Refresh `graphify-out/` after structural changes.
- **Strict Layering**: `contracts/` and `core/` never import FastAPI, CrewAI, LangGraph, Google GenAI, or PyMongo (enforced via AST tests in `tests/test_invariants.py`).
- **Read-Only Triage & Immutability**: Agents never execute live actions; Safety Reviewer gets zero tools; all DTOs use `ConfigDict(frozen=True)` and `model_copy(update=...)`.
- **Defense-in-Depth & Offline-First**: Timing-safe `API_AUTH_TOKEN` (`401`), sliding-window rate limit (`429`), size (`413`), MIME (`415`), path-safe IDs (`400`), `<untrusted_context>` framing, and offline-by-default `pytest` (`branch = true`).
