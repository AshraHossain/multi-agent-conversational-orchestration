# Task Backlog — `ma_co`

Live engineering backlog tracked alongside [PLAN.md](PLAN.md) and [PLANNING.md](PLANNING.md).

## Done
- [x] Freeze all Pydantic DTOs with `ConfigDict(frozen=True)` and immutable `tuple`/`frozenset` collections.
- [x] Implement defense-in-depth FastAPI middleware (`401` timing-safe auth & HMAC webhook signing, `429` bounded sliding-window rate limit, `413` size cap, `415` MIME check, `400` path-traversal rejection, `Idempotency-Key` replay/conflict, OWASP + telemetry headers).
- [x] Add `<untrusted_context>` XML boundary framing, `sanitize_identifier`, `redact_secrets`, SHA-256 `compute_audit_digest` chaining, read-only execution-claim veto, and evidence grounding overlap veto.
- [x] Migrate `GenaiJudge`/`GenaiRegenerator` to official `google-genai` SDK with structured JSON output and token-based USD cost estimation; enable `mypy --strict` across all `src/ma_co/adapters/`.
- [x] Add `RuntimeBundle` DI wiring (`api/runtime.py`), pluggable read-only `TelemetryProvider`s (`tools/providers.py`), and `MongoRunStore` indexing/`list_runs`/`is_ready`.
- [x] Add `GET /v1/runs` filtering/pagination, `POST /v1/incidents/triage/async` (`202 Accepted`), `GET /v1/runs/{run_id}/stream` (SSE), `POST /v1/runs/{run_id}/follow-up` (immutable child runs), and preserved review audit metadata (`reviewed_by`, `review_decision`, `review_note`, `reviewed_at`).
- [x] Add unified Prometheus `/metrics` endpoint and optional OpenTelemetry `start_span` (`src/ma_co/telemetry.py`).
- [x] Build self-contained offline Incident Cockpit Web UI (`GET /cockpit`) with route-scoped CSP, live SSE streaming, draft diff viewer, follow-up form, and human review queue.
- [x] Expand golden evaluation dataset to 20 versioned cases (`evaluation/datasets/golden_cases.jsonl`), isolate eval `RunStore` to temp dir, add 12/12 guardrails, 92/92 red-team matrix, and `--live` Tier-3 blind-spot replay scaffolding.
- [x] Harden CI workflow with live Docker container smoke test (`/readyz`, `/cockpit`, `/v1/incidents/triage`) and add optional `mongo`/`observability` profiles to `docker-compose.yml`.

## Next (Requires Live Cloud Budget Approval)
- [ ] Run Tier-3 live evaluation (`uv run python -m ma_co.eval --live --repeat 3`) against live Gemini (`GOOGLE_API_KEY`) / Bynara (`BYNARA_API_KEY`) and archive results in `docs/eval_live_baseline.md` once cloud token budget is approved.
