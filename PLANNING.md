# Architecture & Planning (`ma_co`)

## Design Principles

1. **Deterministic Core vs. AI Layering**: Policy caps (`max_regenerations`, `max_estimated_cost_usd`, `forbidden_tools`), draft validation (`validate_incident_draft`), identifier sanitization (`sanitize_identifier`), and prompt-injection framing (`frame_untrusted_text`) live in pure Python functions under `src/ma_co/core/`.
2. **Immutability**: All Pydantic DTOs in `src/ma_co/core/models.py` use `ConfigDict(frozen=True)`. State transitions in `ReflectionEngine` and `/v1/runs/{run_id}/review` construct new records via `model_copy(update=...)`.
3. **Read-Only Triage Boundary**: Neither CrewAI agents nor the FastAPI `/review` endpoint can trigger rollbacks, deployments, or external notifications.
4. **Offline-First Verification**: All unit, integration, security, and evaluation tests run 100% offline (`CREWAI_MOCK=1` and `FixtureJudge`/`FixtureRegenerator`), while live provider tests are isolated behind `@pytest.mark.live`.

## Layered Architecture (`flowchart LR`)

```mermaid
flowchart LR
    subgraph Client["Client & CI Surface"]
        CLI["CLI (ma_co.cli)"]
        API_C["HTTP Clients / Eval"]
    end
    subgraph Edge["Edge & Guardrails"]
        MW["Auth (401) + Rate Limit (429) + Size (413) + MIME (415)"]
    end
    subgraph Core["Deterministic Pure Core"]
        VAL["validation.py"]
        REF["reflection.py"]
        STR["store.py"]
    end
    subgraph Adapters["Isolated Adapters"]
        CRW["crewai_incident.py"]
        LGR["langgraph_reflection.py"]
        GEN["genai_adapter.py"]
        MGO["mongo_store.py"]
    end
    CLI & API_C --> MW --> VAL --> REF --> STR
    REF --> LGR
    CLI --> CRW
    REF -. "Live" .-> GEN
    STR -. "Live" .-> MGO
```

## Runtime Sequence (`sequenceDiagram`)

```mermaid
sequenceDiagram
    autonumber
    participant Caller
    participant FastAPI as api/main.py
    participant Engine as core/reflection.py
    participant Validator as core/validation.py
    participant Store as core/store.py

    Caller->>FastAPI: POST /v1/incidents/triage
    FastAPI->>Validator: sanitize_identifier(incident_id)
    FastAPI->>Engine: run(incident, initial_draft)
    Engine->>Validator: apply_deterministic_veto(incident, draft)
    Engine-->>FastAPI: Immutable RunRecord
    FastAPI->>Store: save(RunRecord)
    FastAPI-->>Caller: 201 Created + OWASP Headers
```

## References

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Component contracts and tool schemas
- [docs/DECISIONS.md](docs/DECISIONS.md) — CrewAI and LangGraph orchestration rationale
- [docs/PLAN.md](docs/PLAN.md) — Four-week implementation milestones
