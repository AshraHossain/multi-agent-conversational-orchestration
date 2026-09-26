# Multi-agent conversational orchestration

A uv-managed, incident-response starter that combines a read-only three-agent CrewAI crew with a bounded LangGraph reflection adapter and a SRAF-style policy engine. Fixture-only by default; no actual rollback, deployment, or email sends.

## Setup (existing empty repo)
Run the supplied bootstrap shell script from anywhere; it targets `/Users/ashrafhossain/AI_Engineering_Cockpit/projects/multi-agent-conversational-orchestration` by default. It checks for an existing `.git` checkout and refuses non-empty checkouts. It does not clone, commit, push, or install dependencies.

```sh
cd /Users/ashrafhossain/AI_Engineering_Cockpit/projects/multi-agent-conversational-orchestration
uv sync --group dev
uv run pytest -q
uv run uvicorn ma_co.api.main:app --reload
# other terminal:
curl -s http://127.0.0.1:8000/healthz
curl -s -X POST http://127.0.0.1:8000/v1/incidents/triage -H 'Content-Type: application/json' -d '{"incident_id":"INC-001","alert":"Elevated errors","evidence":["Prometheus 5xx rate 12%"],"proposed_action":"Review rollback"}'
uv run python -m ma_co.cli
```

Install optional adapters with `uv sync --group dev --extra crewai --extra langgraph`; this resolves and writes `uv.lock`, which should be committed. Live CrewAI execution requires `BYNARA_API_KEY` and `uv run --env-file .env python -m ma_co.cli --live-crewai`; it may incur provider costs. The final judge remains a fixture even for live crew output. Optional graph example:

```python
from ma_co.adapters.langgraph_reflection import build_graph
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator
from ma_co.core.models import Policy
from pathlib import Path
import json
state = {"incident": json.loads(Path("evaluation/datasets/incident.json").read_text()), "draft": "Initial triage"}
print(build_graph(FixtureJudge(), FixtureRegenerator(), Policy()).invoke(state))
```

Architecture, tool and endpoint contracts: `docs/ARCHITECTURE.md`; orchestration decisions: `docs/DECISIONS.md`; prompts: `prompts/agents.md`; four-week milestones: `docs/PLAN.md`.

## Security boundary
`/review` is a **demo decision recorder**, not authentication or permission to execute changes. Local JSON run files may contain sensitive text; never feed live confidential incidents without encryption, redaction, retention policy, access controls, and separate trusted execution approval. Fixture scores are synthetic and cannot establish accuracy or cost savings. Keep production code and upstream contributions independently reviewed.
