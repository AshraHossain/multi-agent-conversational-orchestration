# Plan — Multi-Agent Conversational Orchestration (`ma_co`)

Design rationale, architectural boundaries, and phase roadmap for `multi-agent-conversational-orchestration`.
Process definition lives in [PLANNING.md](PLANNING.md); live backlog lives in [TASK.md](TASK.md).

## 1. Layered Architecture Rationale

`ma_co` enforces a strict four-layer boundary so every policy threshold, validation veto, and security guardrail is 100% deterministic, offline-testable, and immune to prompt drift:

| Layer | Package | Responsibility | Framework Imports |
|---|---|---|---|
| **Contracts** | `src/ma_co/contracts/` | Frozen Pydantic schemas (`ConfigDict(frozen=True)`), bounded inputs, immutable `RunRecord`, `FollowUpInput`, `RunListResponse`, `Policy` & `ApprovalInput` DTOs | **Forbidden** |
| **Pure Core** | `src/ma_co/core/` | Deterministic draft validators (ID, evidence grounding, read-only claim veto), `redact_secrets`, SHA-256 `compute_audit_digest`, `<untrusted_context>` framing, bounded `ReflectionEngine`, `RunStoreProtocol` & atomic `RunStore` | **Forbidden** |
| **Adapters & Tools** | `src/ma_co/adapters/`, `src/ma_co/tools/` | CrewAI 3-agent crew (`CREWAI_MOCK=1`), LangGraph bounded reflection state machine, modern `google-genai` judge/regenerator, `MongoRunStore`, pluggable read-only `TelemetryProvider`s | Allowed (strict `mypy`) |
| **API / Telemetry / UI / Eval** | `src/ma_co/api/`, `telemetry.py`, `cli.py`, `eval.py` | FastAPI security middleware (`401` auth/HMAC, `409` idempotency, `413`/`415`/`429`, OWASP headers), runtime DI, async `202`, SSE `/stream`, `/follow-up`, `/runs`, `/metrics`, `/cockpit` UI, 20-case 3-tier eval harness | Thin boundary |

Architecture Decision Records live in [docs/adr/](docs/adr/).

## 2. Phase Roadmap (GSD Milestones)

| Phase | Scope | Acceptance Gate | Status |
|---|---|---|---|
| **Phase 0 — Starter** | FastAPI triage endpoint, CrewAI/LangGraph adapters, fixture tests | `uv run pytest` passes | Done |
| **Phase 1 — Governance & ADRs** | `PLAN.md`, `TASK.md`, `PLANNING.md` (GSD → Superpowers → Ruflo), `docs/adr/`, `.claude/rules/contracts.md` | Agent docs <100 lines, ADRs committed | Done |
| **Phase 2 — `contracts/` & Invariants** | Extract `src/ma_co/contracts/`, enable branch coverage (`branch = true`), add `ruff format --check` + `W`/`SIM`/`RUF`, AST isolation & tool-allowlist tests | `make lint && make typecheck && make test` | Done |
| **Phase 3 — 3-Tier Eval Harness** | Upgrade `ma_co.eval` with `--guardrails`, `--verifier-matrix`, and `--repeat N` statistics | `uv run python -m ma_co.eval --guardrails --verifier-matrix --repeat 3` | Done |
| **Phase 4 — Showcase & Graphify** | Update `README.md` with triad Mermaid diagrams + 3-tier scorecard, refresh `graphify-out/`, tag `v0.2.0` | `make check` green + `v0.2.0` tagged | Done |
| **Phase 5 — v0.3.0 Productionization, Conversational Streaming & Cockpit** | Runtime DI wiring, `google-genai` structured output & token costing, strict `mypy` on adapters, stronger deterministic validators + `redact_secrets` + `audit_digest`, pluggable read-only `TelemetryProvider`s, `Idempotency-Key` + HMAC webhook guard, `GET /v1/runs`, async `202` + SSE `/stream`, `/follow-up`, `/metrics` + OTLP spans, Incident Cockpit UI (`/cockpit`), 20-case JSONL eval dataset + isolated eval store, Docker CI smoke test | `make check` green (strict mypy across 25 files, >=90% branch cov, 20/20 eval, 12/12 guardrails, 92/92 red-team) | Done |
