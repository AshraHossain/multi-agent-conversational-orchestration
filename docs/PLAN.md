# Four-week implementation plan

| Week | Deliverable | Acceptance criterion |
|---|---|---|
| 1 | uv environment, FastAPI, schemas, policy, fixture tests | API returns traceable bounded run; CI green |
| 2 | Three-agent CrewAI live demo, read-only connectors, prompt/version tests | Sample incident produces triage, investigation and reviewer critique; no writes |
| 3 | LangGraph reusable reflection subgraph, provider-backed independent judge, trace store | Low scores retry at most twice; budget/unsupported claims fail closed |
| 4 | Blinded human-labeled benchmark, threat model, docs, upstream PR | Report paired baseline/reflective quality, real cost and errors with confidence intervals |

Avoid claiming production readiness until provider accounting, security reviews, auth, tenant isolation, durable persistence, and action approval are implemented and tested.
