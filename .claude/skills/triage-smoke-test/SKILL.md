---
name: triage-smoke-test
description: Use this skill to verify the incident triage CLI, FastAPI `/v1/incidents/triage` endpoint, security guardrails, and evaluation scorecard offline.
---
# Incident Triage Smoke Test & Verification
1. Run `uv run ruff check .` to verify zero lint and Bandit (`S`) security findings.
2. Run `uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80` to verify offline unit and integration tests.
3. Run `uv run python -m ma_co.cli` (and `CREWAI_MOCK=1 uv run python -m ma_co.cli --live-crewai`) to verify the CLI reflection pipeline offline.
4. Run `uv run python -m ma_co.eval` to generate `evaluation/eval_report.json` and confirm 100% recall, grounding, and guardrail pass rates.
