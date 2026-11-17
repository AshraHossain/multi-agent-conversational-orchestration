# Security Policy

## Reporting a Vulnerability

Open a GitHub Security Advisory or email `security@example.com`. Do not open a public issue. We aim to acknowledge within 48 hours and patch within 14 days for critical issues.

## Threat Model

| Surface | Control | Implementation |
|---------|---------|---------------|
| API auth bypass | Timing-safe key comparison | `hmac.compare_digest` on `X-API-Key` |
| Brute-force | Sliding-window rate limit (per IP) | `_check_rate_limit` in `api/main.py` |
| Oversized payload | 413 before body is read | `content-length` check in middleware |
| Wrong MIME type | 415 on non-JSON mutations | `content-type` check in middleware |
| Path traversal in run IDs | Sanitize before filesystem access | `sanitize_identifier()` in `core/validation.py` |
| Prompt injection | Frame untrusted input | `frame_untrusted_text()` in `core/validation.py` |
| Clickjacking | X-Frame-Options: DENY | OWASP middleware header |
| MIME sniffing | X-Content-Type-Options: nosniff | OWASP middleware header |
| Information leakage via cache | Cache-Control: no-store | OWASP middleware header |
| Container privilege escalation | Non-root UID 10001 | Dockerfile `USER appuser` |
| Secret exposure | Environment variables only | `.env.example`; never committed |

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` | Yes |

## Out of Scope

- Denial-of-service at the infrastructure level (Kubernetes/load-balancer responsibility)
- Issues in direct dependencies — report to those projects
