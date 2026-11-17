# Security Policy & Threat Model

## Threat Model & Mitigations

| Threat Vector | Risk | Mitigation Implemented |
|---|---|---|
| **Indirect Prompt Injection via Incident Alerts / Evidence** | Malicious instructions inside `alert` or `evidence` attempting to hijack CrewAI or Gemini evaluation/regeneration. | `frame_untrusted_text()` in `ma_co/core/validation.py` neutralizes XML escape tags (`</untrusted_context>`) and wraps untrusted payloads inside `<untrusted_context>` data boundaries with explicit instructions to treat contents as passive data. |
| **Unauthorized API Access (`401`)** | Unauthenticated callers invoking `/v1/incidents/triage`, `/v1/runs/{id}`, or `/review`. | Timing-safe token verification (`hmac.compare_digest`) via `X-API-Key` or `Authorization: Bearer <token>` when `API_AUTH_TOKEN` is set, while keeping `/health`, `/healthz`, and `/readyz` unauthenticated for container probes. |
| **Abuse / Denial of Wallet (`429`)** | Burst traffic exhausting reflection loops or LLM budgets. | Sliding-window rate limiter (`RATE_LIMIT_PER_MINUTE`, default `120` req/min) returning `HTTP 429 Too Many Requests` with `Retry-After: 60`. |
| **Unbounded Payload / DoS (`413`)** | Oversized JSON bodies exhausting memory. | Middleware enforces `MAX_PAYLOAD_BYTES` (default `1,048,576` bytes / 1 MB) on `POST` requests (`HTTP 413`), alongside Pydantic `max_length` bounds on `IncidentInput`. |
| **Unsupported Content-Type (`415`)** | Non-JSON payloads submitted to API endpoints. | Middleware enforces `Content-Type: application/json` on `POST` requests (`HTTP 415 Unsupported Media Type`). |
| **Path Traversal & Identifier Injection (`400`)** | Malicious `run_id` or `incident_id` values (`../../etc/passwd`) targeting local JSON storage. | `RunStore` validates strict UUID format and resolves paths within `self.directory.resolve()`. `POST /v1/incidents/triage` rejects `/`, `\`, and `..` in `incident_id` (`HTTP 400`), and `sanitize_identifier()` strips unsafe characters. |
| **Autonomous Remediation / Unbounded Cost** | Agents executing destructive rollbacks/deploys or looping indefinitely. | Agents are strictly read-only; `/v1/runs/{id}/review` only records human decisions. `ReflectionEngine` and `langgraph_reflection` enforce hard `max_regenerations`, `max_estimated_cost_usd`, and `forbidden_tools` policy gates. |
| **OWASP HTTP Response Hardening** | MIME sniffing, clickjacking, or caching of sensitive incident records. | Middleware attaches `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, and `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`. |
| **Static Security Scanning (`S` / Bandit)** | Insecure Python constructs introduced in PRs. | Ruff flake8-bandit (`S`) rules enabled in `pyproject.toml` and enforced in CI. |
| **Container Privilege Escalation** | Running the FastAPI server as `root` inside Docker. | Multi-stage `Dockerfile` runs as unprivileged `appuser` (`UID 10001`). |

## Reporting a Vulnerability

Please report security issues privately via GitHub Security Advisories rather than opening a public issue.
