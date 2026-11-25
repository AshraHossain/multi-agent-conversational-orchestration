# Plan — Multi-Agent Conversational Orchestration (`ma_co`)

Design rationale, architectural boundaries, and phase roadmap for `multi-agent-conversational-orchestration`.
Process definition lives in [PLANNING.md](PLANNING.md); live backlog lives in [TASK.md](TASK.md).

## 1. Layered Architecture Rationale

`ma_co` enforces a strict four-layer boundary so every policy threshold, validation veto, and security guardrail is 100% deterministic, offline-testable, and immune to prompt drift:

| Layer | Package | Responsibility | Framework Imports |
|---|---|---|---|
| **Contracts** | `src/ma_co/contracts/` | Frozen Pydantic schemas (`ConfigDict(frozen=True)`), bounded inputs, immutable `RunRecord` & `Policy` DTOs | **Forbidden** |
| **Pure Core** | `src/ma_co/core/` | Deterministic draft validators, `<untrusted_context>` framing, identifier sanitization, bounded `ReflectionEngine`, atomic `RunStore` | **Forbidden** |
| **Adapters** | `src/ma_co/adapters/` | Thin CrewAI 3-agent crew (`CREWAI_MOCK=1`), LangGraph bounded reflection state machine, Gemini judge/regenerator, MongoDB store | Allowed |
| **API / CLI / Eval** | `src/ma_co/api/`, `cli.py`, `eval.py` | FastAPI security middleware (`401`/`413`/`415`/`429`, OWASP headers), CLI entrypoint, 3-tier evaluation harness | Thin boundary |

Architecture Decision Records live in [docs/adr/](docs/adr/).

## 2. Phase Roadmap (GSD Milestones)

| Phase | Scope | Acceptance Gate | Status |
|---|---|---|---|
| **Phase 0 — Starter** | FastAPI triage endpoint, CrewAI/LangGraph adapters, fixture tests | `uv run pytest` passes | Done |
| **Phase 1 — Governance & ADRs** | `PLAN.md`, `TASK.md`, `PLANNING.md` (GSD → Superpowers → Ruflo), `docs/adr/`, `.claude/rules/contracts.md` | Agent docs <100 lines, ADRs committed | Done |
| **Phase 2 — `contracts/` & Invariants** | Extract `src/ma_co/contracts/`, enable branch coverage (`branch = true`), add `ruff format --check` + `W`/`SIM`/`RUF`, AST isolation & tool-allowlist tests | `make lint && make typecheck && make test` | Done |
| **Phase 3 — 3-Tier Eval Harness** | Upgrade `ma_co.eval` with `--guardrails` (10 perturbations), `--verifier-matrix` (planted defects vs. clean runs), and `--repeat N` statistics | `uv run python -m ma_co.eval --guardrails --verifier-matrix --repeat 3` | Done |
| **Phase 4 — Showcase & Graphify** | Update `README.md` with triad Mermaid diagrams + 3-tier scorecard, refresh `graphify-out/`, run `make check` | `make check` green + `graphify-out/` updated | Done |
