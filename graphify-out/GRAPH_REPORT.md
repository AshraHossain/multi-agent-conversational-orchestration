# Graph Report - multi-agent-conversational-orchestration  (2026-11-27)

## Corpus Check
- Corpus is ~24,520 words - fits in a single context window. You may not need a graph.

## Summary
- 453 nodes · 1028 edges · 25 communities (20 shown, 1 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 21

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 42 edges
2. `RunRecord` - 25 edges
3. `ReflectionEngine` - 25 edges
4. `run_eval()` - 25 edges
5. `FixtureJudge` - 23 edges
6. `Policy` - 22 edges
7. `FixtureRegenerator` - 22 edges
8. `test_mongo_run_store_offline_double()` - 20 edges
9. `RunStore` - 19 edges
10. `triage_async()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_crewai_live_wiring_offline_double()` --calls--> `run_crew()`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/crewai_incident.py
- `test_genai_judge_live()` --uses--> `GenaiJudge`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/genai_adapter.py
- `test_save_overwrites()` --calls--> `utc_now()`  [INFERRED]
  tests/test_store.py → src/ma_co/contracts/incident.py
- `test_mongo_run_store_offline_double()` --calls--> `Policy`  [INFERRED]
  tests/test_adapters.py → src/ma_co/contracts/incident.py
- `test_evidence_marker_cannot_override_defects()` --calls--> `Policy`  [INFERRED]
  tests/test_validation.py → src/ma_co/contracts/incident.py

## Import Cycles
- None detected.

## Communities (25 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (55): build_graph(), evaluate(), Graph owns the bounded loop; action execution is deliberately outside the graph., Build a bounded reflection state machine using LangGraph or pure fallback., main(), Offline-default CLI entrypoint for policy-gated incident triage., Policy, Deterministic reflection and safety policy constraints. (+47 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (46): Opt-in 3-agent CrewAI adapter with CREWAI_MOCK=1 offline fallback., Run the sequential Triager -> Investigator -> Safety Reviewer crew., run_crew(), _run_mock_crew(), _create_genai_client(), _estimate_usage_cost(), _extract_json_payload(), GenaiJudge (+38 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (20): MongoRunStore, MongoDB-backed RunStore conforming to RunStoreProtocol., Terminal and intermediate lifecycle states for an incident triage run., Immutable persisted record of an incident triage run., RunRecord, Status, Path, Protocol (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (39): TestClient, _clean_env_and_rate_limiter(), CaptureFixture, fixture, integration, MonkeyPatch, Path, unit (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (40): configure_runtime(), Swap active runtime dependencies (store, policy, engine, telemetry)., Clear sliding-window rate limiter state (intended for test isolation)., reset_rate_limiter(), Immutable dependency container assembled from environment configuration., RuntimeBundle, _aggregate_stats(), EvalCase (+32 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (19): BaseModel, datetime, model_validator, _run_background_triage(), _on_iter(), ApprovalInput, FollowUpInput, Iteration (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (20): Return factual/structural/safety defects that must block the quality gate., validate_incident_draft(), lookup_event(), TelemetrySource, Read-only fixture telemetry. Live connectors belong behind scoped service…, Lookup a read-only fixture signal for an incident., unit, Unit tests for deterministic validation, secret redaction, sanitization, and… (+12 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (9): Observability re-exports backed by ma_co.telemetry., MetricsRegistry, _NoOpSpan, Any, Lightweight Prometheus metrics registry and optional OpenTelemetry span helper., Zero-overhead fallback span used when opentelemetry is not installed., Start an OpenTelemetry span when opentelemetry-api is installed, else no-op., Thread-safe Prometheus text exposition metrics registry. (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (9): _FallbackGraph, InvokableGraph, Any, Protocol, Minimal protocol shared by compiled LangGraph StateGraph and pure fallback., Pure-Python fallback when langgraph is not installed., State, test_fallback_graph_runs_without_langgraph() (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.19
Nodes (11): BackgroundTasks, Header, _check_idempotency(), _incident_payload_hash(), Run bounded reflection triage synchronously and persist the immutable RunRecord., Accept an incident for asynchronous triage (202 Accepted); poll…, _sanitize_incident(), triage() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.41
Nodes (11): unit, save() uses staging file so a crash mid-write can't leave a corrupt file., _record(), _store(), test_atomic_write(), test_get_invalid_uuid_format(), test_get_missing_returns_none(), test_invalid_uuid_rejected() (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.20
Nodes (11): description, post, Query, follow_up(), get_run(), Retrieve a persisted triage run by UUID., Create an immutable child triage run incorporating new operator evidence or…, Record a human approval or rejection decision with chained audit digest (no… (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (10): get, HTMLResponse, PlainTextResponse, healthz(), incident_cockpit(), prometheus_metrics(), Readiness probe verifying active run store health., Expose in-process counters and latencies in Prometheus exposition format. (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (10): middleware, Request, Response, _attach_security_headers(), _extract_token(), Any, Enforce auth, webhook HMAC, rate limiting, MIME/size caps, metrics, and OWASP…, security_and_telemetry_middleware() (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.28
Nodes (8): FastAPI, _check_rate_limit(), _lifespan(), _prune_stale_rate_windows(), Hardened FastAPI boundary for policy-gated incident triage, streaming, and…, Return (allowed, remaining) with bounded memory via stale-key eviction., Deterministically redact common API tokens, keys, and emails from text., redact_secrets()

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (5): LogRecord, configure_logging(), _JsonFormatter, Structured JSON logging setup. Call configure_logging() at app startup., Wire the root logger to emit JSON on stderr.

### Community 16 - "Community 16"
Cohesion: 0.33
Nodes (6): alias, ge, le, max_length, list_runs(), List persisted triage runs with optional status/incident_id filters and…

### Community 17 - "Community 17"
Cohesion: 0.33
Nodes (3): Exercise full CrewAI agent/task/tool wiring offline via SDK doubles., test_crewai_live_wiring_offline_double(), _tool()

### Community 18 - "Community 18"
Cohesion: 0.50
Nodes (3): Stream Server-Sent Events (SSE) for a run's iterations until terminal status., stream_run(), StreamingResponse

### Community 19 - "Community 19"
Cohesion: 0.67
Nodes (3): live, Requires GOOGLE_API_KEY in environment., test_genai_judge_live()

## Knowledge Gaps
- **1 isolated node(s):** `multi-agent-conversational-orchestration`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 168 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `Community 9` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 5`, `Community 6`, `Community 10`, `Community 17`, `Community 19`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `run_eval()` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 6`, `Community 9`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `test_mongo_run_store_offline_double()` connect `Community 2` to `Community 0`, `Community 9`, `Community 1`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `IncidentInput` (e.g. with `test_crewai_live_wiring_offline_double()` and `test_crewai_mock_offline()`) actually correct?**
  _`IncidentInput` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ReflectionEngine` (e.g. with `execute_triage()` and `RuntimeBundle`) actually correct?**
  _`ReflectionEngine` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `TestClient` (e.g. with `test_api_review_never_executes_action_and_chains_audit_digest()` and `test_api_review_reject_and_run_lookup_errors()`) actually correct?**
  _`TestClient` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `multi-agent-conversational-orchestration` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._