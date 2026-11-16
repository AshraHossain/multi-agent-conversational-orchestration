---
name: triage-smoke-test
description: Use this skill to verify the incident triage CLI and FastAPI `/v1/incidents/triage` endpoint offline.
---
# Incident Triage Smoke Test
1. Run `uv run pytest -q`.
2. Run `uv run python -m ma_co.cli` to verify the bounded reflection pipeline offline.
