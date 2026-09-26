# Architecture and component contracts

```text
Alert/event -> FastAPI ingestion -> validation -> incident record
                                    -> CrewAI triage -> investigation -> reviewer (opt-in live CLI)
                                    -> SRAF-style judge -> bounded regenerate -> quality decision
                                    -> review record -> [separate future authenticated executor]
                                    -> JSON trace / benchmark dataset / dashboard
LangGraph adapter: evaluate -> (pass/limit -> finish | fail -> regenerate -> evaluate)
```

## Component boundaries
| Component | Input | Output | Failure handling |
|---|---|---|---|
| API | IncidentInput | RunRecord + run_id | Reject invalid inputs; fail closed |
| CrewAI crew | Alert + read-only fixture signals | Draft + reviewer feedback | Provider failure must not trigger an action |
| Judge | IncidentInput + draft | Score, critique, evidence gaps, cost | Invalid response fails run |
| Policy router | Score, gaps, cost, count | Retry or stop | Hard cap on retries and budget |
| Approval recorder | Run ID + reviewer decision | Updated run | No external execution |
| Future executor | Approved signed action + scoped identity | Audited action receipt | Idempotency and deny by default |

## API
| Method | Route | Purpose |
|---|---|---|
| GET | /healthz | Liveness |
| POST | /v1/incidents/triage | Local fixture draft, evaluate, persist |
| GET | /v1/runs/{run_id} | Read run history |
| POST | /v1/runs/{run_id}/review | Record demo approval/rejection; no execution |

Example request: `{"incident_id":"INC-001","alert":"5xx spike","evidence":["Prometheus: 12% at 10:05 UTC"],"proposed_action":"Review rollback"}`.
Future production API should add authn/authz, idempotency keys, asynchronous workers and a distinct signed execution request.

## Tool contracts
`lookup_event(incident_id: str, source: Literal["prometheus", "github", "kubernetes"]) -> str` is read-only fixture access. Future connectors return `{source_id, observed_at, payload_digest, content, classification}`; enforce tenant and RBAC in the tool service, not prompts. Never grant the reviewer an execution tool.
