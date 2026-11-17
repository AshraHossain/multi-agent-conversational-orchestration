---
paths:
  - "src/ma_co/api/**/*.py"
  - "src/ma_co/adapters/**/*.py"
---
# `ma_co` API & Adapter Rules (`src/ma_co/api/`, `src/ma_co/adapters/`)
1. Keep routes in `api/main.py` thin; delegate validation, reflection, and persistence to `ma_co/core/`.
2. Enforce timing-safe auth (`hmac.compare_digest` when `API_AUTH_TOKEN` is set), sliding-window rate limiting (`RATE_LIMIT_PER_MINUTE`), payload size caps (`413`), `application/json` MIME checks (`415`), and OWASP response headers on all API responses while keeping `/health`, `/healthz`, and `/readyz` open for probes.
3. Frame untrusted incident alert and evidence fields with `<untrusted_context>` before passing to CrewAI or LLM adapters, and support deterministic offline execution (`CREWAI_MOCK=1`).
