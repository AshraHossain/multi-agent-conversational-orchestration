# Graph Report - multi-agent-conversational-orchestration  (2026-11-16)

## Corpus Check
- Corpus is ~10,982 words - fits in a single context window. You may not need a graph.

## Summary
- 248 nodes · 569 edges · 15 communities (10 shown, 1 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 106 edges (avg confidence: 0.94)
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
- Community 11

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 48 edges
2. `Policy` - 21 edges
3. `RunRecord` - 20 edges
4. `ReflectionEngine` - 20 edges
5. `FixtureJudge` - 18 edges
6. `FixtureRegenerator` - 16 edges
7. `Status` - 15 edges
8. `build_graph()` - 14 edges
9. `JudgeResult` - 14 edges
10. `test_mongo_run_store_offline_double()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_langgraph_graph_builds()` --calls--> `build_graph()`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/langgraph_reflection.py
- `test_save_overwrites()` --uses--> `Status`  [INFERRED]
  tests/test_store.py → src/ma_co/core/models.py
- `test_evidence_marker_cannot_override_defects()` --uses--> `Status`  [INFERRED]
  tests/test_validation.py → src/ma_co/core/models.py
- `test_mongo_run_store_offline_double()` --uses--> `Policy`  [INFERRED]
  tests/test_adapters.py → src/ma_co/core/models.py
- `test_evidence_marker_cannot_override_defects()` --uses--> `Policy`  [INFERRED]
  tests/test_validation.py → src/ma_co/core/models.py

## Import Cycles
- None detected.

## Communities (15 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (28): live, Opt-in 3-agent CrewAI adapter with CREWAI_MOCK=1 offline fallback., Run the sequential Triager -> Investigator -> Safety Reviewer crew., run_crew(), read_incident_signal(), _run_mock_crew(), GenaiJudge, GenaiRegenerator (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (29): get, middleware, post, Request, Response, MongoRunStore, Optional MongoDB-backed RunStore. Requires pymongo and MONGO_URI env var., MongoDB-backed RunStore. Same interface as core.store.RunStore. (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (29): main(), Offline-default CLI entrypoint for policy-gated incident triage., Policy, Terminal and intermediate lifecycle states for an incident triage run., Deterministic reflection and safety policy constraints., Status, FixtureJudge, FixtureRegenerator (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (20): BaseModel, datetime, Protocol, build_graph(), evaluate(), Graph owns the bounded loop; action execution is deliberately outside the graph., Build a bounded reflection state machine using LangGraph or pure fallback., Iteration (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.19
Nodes (15): Path, Thread-safe local JSON RunStore with path-traversal protection., Small local dev store. Use durable DB + transactions for production., RunStore, unit, save() uses staging file so a crash mid-write can't leave a corrupt file., _record(), _store() (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.16
Nodes (16): Any, Clear sliding-window rate limiter state (intended for test isolation)., reset_rate_limiter(), EvalCase, main(), Path, Deterministic evaluation & latency benchmark harness for ma_co. Run via: uv run…, Immutable specification of a single incident triage benchmark case. (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.20
Nodes (16): model_validator, ApprovalInput, Human reviewer decision payload for /v1/runs/{run_id}/review., Return factual/structural defects that must block the quality gate., validate_incident_draft(), unit, Unit tests for deterministic validation, sanitization, and fixture tools., sample_incident() (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.21
Nodes (14): CaptureFixture, fixture, _clean_env_and_rate_limiter(), integration, MonkeyPatch, Path, Integration tests for FastAPI security middleware, endpoints, CLI, and eval…, test_api_review_never_executes_action() (+6 more)

### Community 8 - "Community 8"
Cohesion: 0.26
Nodes (11): unit, Security branch coverage: 401, 413, 415, 429, path traversal., test_missing_token_401(), test_no_auth_token_allows_all(), test_oversized_payload_413(), test_path_traversal_in_run_id_400(), test_probe_bypasses_auth(), test_rate_limit_429() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (5): _FallbackGraph, Pure-Python fallback when langgraph is not installed., State, test_fallback_graph_runs_without_langgraph(), TypedDict

## Knowledge Gaps
- **1 isolated node(s):** `multi-agent-conversational-orchestration`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 89 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Why does `RunRecord` connect `Community 1` to `Community 2`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `run_eval()` connect `Community 5` to `Community 0`, `Community 6`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `IncidentInput` (e.g. with `run_crew()` and `_run_mock_crew()`) actually correct?**
  _`IncidentInput` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Policy` (e.g. with `build_graph()` and `main()`) actually correct?**
  _`Policy` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RunRecord` (e.g. with `MongoRunStore` and `get_run()`) actually correct?**
  _`RunRecord` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ReflectionEngine` (e.g. with `IncidentInput` and `Iteration`) actually correct?**
  _`ReflectionEngine` has 13 INFERRED edges - model-reasoned connections that need verification._