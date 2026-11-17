# Multi-Agent Conversational Orchestration

[![CI](https://github.com/AshraHossain/multi-agent-conversational-orchestration/actions/workflows/ci.yml/badge.svg)](https://github.com/AshraHossain/multi-agent-conversational-orchestration/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage ≥80%](https://img.shields.io/badge/coverage-%E2%89%A580%25-brightgreen)](https://github.com/AshraHossain/multi-agent-conversational-orchestration)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.100+-blue.svg)](https://www.crewai.com)

Policy-gated incident-response orchestration service. Combines a read-only three-agent **CrewAI** crew, a bounded **LangGraph** reflection state machine, a deterministic **SRAF-style policy & quality gate engine**, and a hardened **FastAPI** API.

> **Safety boundary**: Agents never execute rollbacks, deployments, or emails. All actions are proposed and require explicit human review. The `/review` endpoint records decisions only.

## Evaluation Scorecard

| Metric | Value |
|---|---|
| Recall@1 (score ≥ 0.8) | 1.00 |
| Grounding rate | 1.00 |
| Guardrail pass rate | 1.00 |
| Latency p50 | < 1 ms |
| Latency p95 | < 5 ms |

*Fixture-based offline scores. See `evaluation/eval_report.json` after `make eval`.*

## Architecture

### Layered System Architecture

```mermaid
flowchart LR
    subgraph Edge["Edge / Security Middleware"]
        A[X-API-Key Auth\nhmac.compare_digest]
        B[Sliding-Window\nRate Limiter]
        C[MIME + Size\nGuards]
        D[OWASP Headers]
    end

    subgraph Router["Thin FastAPI Routers"]
        E[POST /v1/incidents/triage]
        F[GET /v1/runs/:id]
        G[POST /v1/runs/:id/review]
        H[GET /health /healthz /readyz]
    end

    subgraph Core["Deterministic Pure Core"]
        I[IncidentInput\nPolicy — frozen DTOs]
        J[validate_incident_draft\nsanitize_identifier\nframe_untrusted_text]
        K[ReflectionEngine\nbounded retry + cost cap]
        L[RunStore\natomic JSON writes]
    end

    subgraph Adapters["Isolated Service Adapters"]
        subgraph Live["Live Cloud"]
            M[GenaiJudge\nGenaiRegenerator\ngoogle-genai]
            N[CrewAI Crew\nBynara / OpenAI-compat]
            O[MongoRunStore\npymongo]
        end
        subgraph Offline["Offline Mock"]
            P[FixtureJudge\nFixtureRegenerator]
            Q[CREWAI_MOCK=1]
            R[File-based RunStore]
        end
    end

    Edge --> Router
    Router --> Core
    Core --> Adapters
```

### End-to-End Request Sequence

```mermaid
sequenceDiagram
    participant Client
    participant Middleware
    participant Router
    participant Engine as ReflectionEngine
    participant Judge
    participant Store

    Client->>Middleware: POST /v1/incidents/triage\n{X-API-Key, Content-Type: application/json}
    Middleware->>Middleware: hmac auth check → 401 if bad
    Middleware->>Middleware: rate-limit check → 429 if exceeded
    Middleware->>Middleware: MIME + size check → 415/413 if bad
    Middleware->>Router: pass request

    Router->>Router: Pydantic validate IncidentInput → 422 if invalid
    Router->>Engine: engine.run(incident, draft)

    loop max_regenerations
        Engine->>Judge: judge.evaluate(incident, draft)
        Judge-->>Engine: JudgeResult(score, critique, missing_evidence)
        Engine->>Engine: validate_incident_draft (deterministic)
        alt score ≥ min_score and no defects
            Engine->>Engine: status = needs_review / approved_draft
        else
            Engine->>Engine: regenerator.regenerate(...)
        end
    end

    Engine-->>Router: RunRecord (frozen, immutable)
    Router->>Store: store.save(record)
    Router-->>Middleware: RunRecord JSON 201
    Middleware->>Middleware: attach OWASP headers + X-Request-ID
    Middleware-->>Client: 201 RunRecord + security headers
```

## Quick Start

```bash
# Install
uv sync --group dev --extra langgraph

# Verify
make check         # lint + test (≥80% cov) + eval harness

# Run
make dev           # uvicorn on :8000

# Triage an incident
curl -s -X POST http://127.0.0.1:8000/v1/incidents/triage \
  -H 'Content-Type: application/json' \
  -d '{"incident_id":"INC-001","alert":"Elevated errors","evidence":["Prometheus 5xx rate 12%"],"proposed_action":"Review rollback"}'

# CLI (offline)
uv run python -m ma_co.cli

# CLI (live CrewAI, requires BYNARA_API_KEY)
CREWAI_MOCK=1 uv run python -m ma_co.cli --live-crewai
```

## Configuration

Copy `.env.example` to `.env` and set the values you need.

| Variable | Default | Purpose |
|---|---|---|
| `API_AUTH_TOKEN` | unset (open) | Enable timing-safe API key auth |
| `GOOGLE_API_KEY` | — | Live google-genai Judge/Regenerator |
| `BYNARA_API_KEY` | — | Live CrewAI crew |
| `MONGO_URI` | — | MongoDB RunStore backend |
| `RATE_LIMIT_PER_MINUTE` | 120 | Sliding-window rate limit |
| `MAX_PAYLOAD_BYTES` | 65536 | Request payload size cap |
| `CREWAI_MOCK` | unset | Set to `1` for offline CrewAI |

## Module Layout

```text
src/ma_co/
  core/
    models.py          # Frozen Pydantic DTOs
    validation.py      # sanitize_identifier, frame_untrusted_text, validate_incident_draft
    reflection.py      # Judge/Regenerator protocols + ReflectionEngine (immutable)
    store.py           # Thread-safe atomic JSON RunStore
  adapters/
    crewai_incident.py      # 3-agent CrewAI crew (CREWAI_MOCK=1 offline)
    langgraph_reflection.py # Bounded LangGraph reflection subgraph
    genai_adapter.py        # google-genai live Judge + Regenerator
    mongo_store.py          # MongoDB-backed RunStore
  api/
    main.py            # FastAPI + security middleware
  tools/
    fixtures.py        # Read-only fixture telemetry
  cli.py               # Offline-default CLI
  eval.py              # Eval harness → evaluation/eval_report.json
```

## Security

See [SECURITY.md](SECURITY.md) for the full threat model and mitigations.

## License

MIT
