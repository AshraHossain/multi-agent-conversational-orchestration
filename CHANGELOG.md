# Changelog

## 0.3.0
- **Runtime Wiring & Modern SDKs**: Added `src/ma_co/api/runtime.py` DI wiring connecting FastAPI to configured stores (`RunStore` / `MongoRunStore`), LLMs (`Fixture` / `google-genai`), and optional 3-agent CrewAI drafting; migrated `genai_adapter.py` to official `google-genai` with structured JSON output and token-based USD cost estimation; enabled `mypy --strict` across all `src/ma_co/adapters/`.
- **Conversational, Async & Streaming API**: Added `POST /v1/incidents/triage/async` (`202 Accepted` background triage), `GET /v1/runs/{run_id}/stream` (SSE), `POST /v1/runs/{run_id}/follow-up` (immutable child runs with `parent_run_id`), `GET /v1/runs` filtering & pagination, `Idempotency-Key` replay/conflict (`200`/`409`), `WEBHOOK_SIGNING_SECRET` HMAC verification (`401`), and preserved human review audit metadata + SHA-256 `audit_digest` chaining.
- **Stronger Deterministic Safety & Telemetry**: Added `redact_secrets`, read-only execution-claim veto, evidence grounding overlap veto, pluggable read-only `TelemetryProvider`s (`src/ma_co/tools/providers.py`), Prometheus `/metrics` + optional OpenTelemetry `start_span` (`src/ma_co/telemetry.py`), and bounded stale-key eviction on the rate limiter.
- **Incident Cockpit UI**: Added self-contained offline operator dashboard at `GET /cockpit` with route-scoped CSP, live SSE progress, iteration timeline, draft diff viewer, follow-up form, and human review queue.
- **20-Case Eval & CI Hardening**: Expanded benchmark to 20 versioned cases (`evaluation/datasets/golden_cases.jsonl`), isolated eval storage to a temp directory, expanded guardrails to 12/12 and verifier red-team matrix to 92/92, added `--live` Tier-3 scaffolding, added live Docker container smoke test to CI, and added optional `mongo`/`observability` profiles to `docker-compose.yml`.

## 0.2.0
- Froze all Pydantic domain models (`ConfigDict(frozen=True)`) and refactored `ReflectionEngine` and `/review` to use immutable `model_copy(update=...)` transitions.
- Added defense-in-depth FastAPI security middleware: timing-safe `API_AUTH_TOKEN` verification (`401`), sliding-window rate limiting (`429`), payload byte caps (`413`), `application/json` MIME checks (`415`), path-traversal protection (`400`), and OWASP + telemetry headers.
- Added `<untrusted_context>` prompt-injection framing (`frame_untrusted_text`) and `sanitize_identifier` in `ma_co.core.validation`.
- Added `CREWAI_MOCK=1` offline fallback in `ma_co.adapters.crewai_incident`, deterministic validation veto in `ma_co.adapters.langgraph_reflection`, and removed duplicate `--live-crewai` execution in `ma_co.cli`.
- Added reproducible evaluation harness (`ma_co.eval`), `Makefile`, non-root `Dockerfile`, `docker-compose.yml`, `SECURITY.md`, `PLANNING.md`, and dual Mermaid architecture diagrams in `README.md`.

## 0.1.0
- Initial policy-gated incident triage starter with FastAPI, CrewAI adapter, LangGraph reflection adapter, and fixture tests.
