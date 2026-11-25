# ADR 0003: Defense-in-Depth FastAPI Boundary & Untrusted Context Framing

## Status
Accepted

## Context
Incident alerts and telemetry payloads originate from external monitoring systems and can contain adversarial prompt-injection strings, oversized bodies, non-JSON payloads, or path-traversal identifiers.

## Decision
1. Enforce edge guardrails in a single FastAPI HTTP middleware layer: timing-safe token auth (`hmac.compare_digest` on `X-API-Key` / `Authorization: Bearer` when `API_AUTH_TOKEN` is set), sliding-window IP rate limiting (`429` + `Retry-After: 60`), `application/json` MIME enforcement (`415`), payload byte ceiling (`413`), and OWASP security + telemetry headers on all responses while leaving `/health`, `/healthz`, and `/readyz` unauthenticated for probes.
2. Reject path-traversal characters (`/`, `\`, `..`) in `incident_id` (`400`) and normalize `run_id` via `UUID` + resolved directory boundary checks in `RunStore`.
3. Neutralize boundary-escape tags and wrap all untrusted alert/draft/critique text inside `<untrusted_context>...</untrusted_context>` XML delimiters via `frame_untrusted_text()` before passing data to LLM adapters.

## Consequences
- Every security boundary is tested deterministically offline in `tests/test_security.py`, `tests/test_api.py`, and the Tier-1 `--guardrails` evaluation harness.
