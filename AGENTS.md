# AGENTS.md — Multi-Agent Conversational Orchestration (ma_co)

Portable instructions for **Antigravity (Gemini)**, **Claude Code**, and other coding agents.

## What this project is
An incident-response orchestration service (`src/ma_co/`) combining a read-only three-agent crew, a bounded LangGraph reflection adapter, a SRAF-style policy engine, and a FastAPI `/v1/incidents/triage` endpoint.

## Commands
```bash
uv sync --group dev                                  # install locked dependencies
uv run pytest -q                                     # run offline test suite
uv run uvicorn ma_co.api.main:app --reload           # run FastAPI triage server
uv run python -m ma_co.cli                           # run offline CLI triage flow
```

## Repo-Specific Rules
- **Read-Only Triage**: Agents never execute live rollbacks, deployments, or emails; all actions are proposed and policy-checked.
- **Fixture-Default Execution**: Default runs use `FixtureJudge` and `FixtureRegenerator` with zero live LLM calls unless `--live-crewai` is explicitly passed.
