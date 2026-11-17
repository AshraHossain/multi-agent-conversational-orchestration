# Changelog

## 0.2.0
- Froze all Pydantic domain models (`ConfigDict(frozen=True)`) and refactored `ReflectionEngine` and `/review` to use immutable `model_copy(update=...)` transitions.
- Added defense-in-depth FastAPI security middleware: timing-safe `API_AUTH_TOKEN` verification (`401`), sliding-window rate limiting (`429`), payload byte caps (`413`), `application/json` MIME checks (`415`), path-traversal protection (`400`), and OWASP + telemetry headers.
- Added `<untrusted_context>` prompt-injection framing (`frame_untrusted_text`) and `sanitize_identifier` in `ma_co.core.validation`.
- Added `CREWAI_MOCK=1` offline fallback in `ma_co.adapters.crewai_incident`, deterministic validation veto in `ma_co.adapters.langgraph_reflection`, and removed duplicate `--live-crewai` execution in `ma_co.cli`.
- Added reproducible evaluation harness (`ma_co.eval`), `Makefile`, non-root `Dockerfile`, `docker-compose.yml`, `SECURITY.md`, `PLANNING.md`, and dual Mermaid architecture diagrams in `README.md`.

## 0.1.0
- Initial policy-gated incident triage starter with FastAPI, CrewAI adapter, LangGraph reflection adapter, and fixture tests.
