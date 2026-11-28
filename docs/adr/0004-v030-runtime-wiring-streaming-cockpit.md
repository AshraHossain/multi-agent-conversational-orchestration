# ADR-0004: v0.3.0 Runtime Wiring, Conversational Async/SSE, Audit Chaining & Incident Cockpit

- **Status**: Accepted
- **Date**: 2026-11-26

## Context
At `v0.2.0`, `ma_co` had isolated adapters (`GenaiJudge`, `MongoRunStore`, `CrewAI`, `LangGraph`), a pure deterministic core, and a hardened synchronous FastAPI edge, but several production gaps remained:
1. FastAPI was hardwired to module-level offline fixtures (`FixtureJudge`, `RunStore`) rather than environment-driven DI.
2. `GenaiJudge`/`GenaiRegenerator` still used the legacy `google-generativeai` package with hardcoded cost estimates, and `src/ma_co/adapters/` was excluded from `mypy --strict`.
3. Triage was single-shot and synchronous; slow live crews needed `202 Accepted` async intake, SSE streaming, and multi-turn operator follow-ups.
4. Operators lacked run listing, Prometheus/OTLP observability, idempotent webhook ingestion (`Idempotency-Key` + HMAC signing), tamper-evident audit digests, and a visual Incident Cockpit UI.

## Decision
1. **Runtime Wiring (`src/ma_co/api/runtime.py`)**: Assemble `RuntimeBundle(store, policy, engine, telemetry, ...)` via env configuration while defaulting 100% offline. Keep `configure_runtime()` for clean test/eval isolation.
2. **Modern SDK & Strict Typing**: Migrate `genai_adapter.py` to `google-genai` with native JSON output config and token-based USD cost estimation from `usage_metadata`; remove `src/ma_co/adapters/` from `mypy` exclusions.
3. **Stronger Pure Deterministic Core**: Add `redact_secrets`, `compute_audit_digest` (tamper-evident SHA-256 chain across creation and human review), read-only execution-claim veto, and evidence grounding overlap veto in `src/ma_co/core/validation.py`.
4. **Conversational & Async API**: Add `GET /v1/runs`, `POST /v1/incidents/triage/async` (`202 Accepted`), `GET /v1/runs/{run_id}/stream` (SSE), `POST /v1/runs/{run_id}/follow-up` (immutable child runs via `parent_run_id`), `Idempotency-Key` replay/conflict (`200`/`409`), and `WEBHOOK_SIGNING_SECRET` HMAC verification (`401`).
5. **Observability & Incident Cockpit**: Add unified `src/ma_co/telemetry.py` (`/metrics` Prometheus exposition + optional OpenTelemetry `start_span`) and a self-contained offline `/cockpit` UI (`src/ma_co/api/cockpit.html`) with route-scoped CSP (`script-src 'self' 'unsafe-inline'` only on `/cockpit`, keeping strict `default-src 'none'` on all API/probe routes).

## Consequences
- Zero breaking changes to existing `v0.2.0` contracts or endpoints.
- Default `make check` remains 100% offline with strict `mypy` across all 25 source modules, `>90%` branch coverage, and 20 versioned golden eval cases (`evaluation/datasets/golden_cases.jsonl`) in an isolated temp store.
