# Graph Report - multi-agent-conversational-orchestration  (2026-11-25)

## Corpus Check
- Corpus is ~14,803 words - fits in a single context window. You may not need a graph.

## Summary
- 286 nodes · 632 edges · 16 communities (11 shown, 1 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 92 edges (avg confidence: 0.89)
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
- Community 12

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 34 edges
2. `Policy` - 21 edges
3. `FixtureJudge` - 20 edges
4. `FixtureRegenerator` - 19 edges
5. `ReflectionEngine` - 19 edges
6. `run_eval()` - 16 edges
7. `RunRecord` - 14 edges
8. `build_graph()` - 13 edges
9. `run_guardrail_suite()` - 13 edges
10. `JudgeResult` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_crewai_mock_offline()` --calls--> `run_crew()`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/crewai_incident.py
- `test_genai_judge_and_regenerator_offline_doubles()` --uses--> `GenaiRegenerator`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/genai_adapter.py
- `test_langgraph_graph_builds()` --calls--> `build_graph()`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/langgraph_reflection.py
- `test_mongo_run_store_offline_double()` --uses--> `MongoRunStore`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/mongo_store.py
- `test_save_overwrites()` --calls--> `utc_now()`  [INFERRED]
  tests/test_store.py → src/ma_co/contracts/incident.py

## Import Cycles
- None detected.

## Communities (16 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (38): main(), Offline-default CLI entrypoint for policy-gated incident triage., Policy, Deterministic reflection and safety policy constraints., FixtureJudge, FixtureRegenerator, Bounded reflection engine and deterministic offline fixture doubles., Deterministic demo only; this is NOT a groundedness evaluator. (+30 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (29): fixture, Clear sliding-window rate limiter state (intended for test isolation)., reset_rate_limiter(), TestClient, _clean_env_and_rate_limiter(), CaptureFixture, integration, MonkeyPatch (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (26): BaseModel, datetime, model_validator, post, get_run(), Run bounded offline reflection triage and persist the immutable RunRecord., Retrieve a persisted triage run by UUID., Record a human approval or rejection decision without executing external… (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (16): Protocol, build_graph(), evaluate(), _FallbackGraph, Graph owns the bounded loop; action execution is deliberately outside the graph., Pure-Python fallback when langgraph is not installed., Build a bounded reflection state machine using LangGraph or pure fallback., State (+8 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (18): Opt-in 3-agent CrewAI adapter with CREWAI_MOCK=1 offline fallback., Run the sequential Triager -> Investigator -> Safety Reviewer crew., run_crew(), read_incident_signal(), _run_mock_crew(), GenaiRegenerator, google-genai live Judge and Regenerator. Requires GOOGLE_API_KEY and the…, Live Regenerator backed by google-generativeai. (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (12): live, GenaiJudge, Live Judge backed by google-generativeai. Falls back to fixture on import error., IncidentInput, Validated incident payload submitted for read-only triage., unit, Offline and live-marked tests for CrewAI, LangGraph, GenAI, and MongoDB…, Requires GOOGLE_API_KEY in environment. (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (21): get, LogRecord, middleware, Request, Response, _attach_security_headers(), _check_rate_limit(), _extract_token() (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (21): _aggregate_stats(), EvalCase, main(), Any, Path, Tier 2: Red-team deterministic veto matrix (planted defects vs. clean drafts)., Immutable specification of a single incident triage benchmark case., Execute the offline golden evaluation suite with optional repeat & red-team… (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.19
Nodes (15): Path, Thread-safe local JSON RunStore with path-traversal protection., Small local dev store. Use durable DB + transactions for production., RunStore, unit, save() uses staging file so a crash mid-write can't leave a corrupt file., _record(), _store() (+7 more)

### Community 9 - "Community 9"
Cohesion: 0.30
Nodes (13): Return factual/structural defects that must block the quality gate., validate_incident_draft(), unit, Unit tests for deterministic validation, sanitization, and fixture tools., sample_incident(), test_evidence_marker_cannot_override_defects(), test_frame_untrusted_text_neutralizes_escape_tags(), test_lookup_event_valid_and_invalid_source() (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.25
Nodes (7): _collect_imports(), Path, Structural, AST layering, immutability, ground-truth, and tool-allowlist…, AST guard: contracts/ and core/ must remain 100% framework- and SDK-free., Every Pydantic model exported by ma_co.contracts must be immutable., test_all_contract_models_are_frozen(), test_core_and_contracts_never_import_frameworks()

## Knowledge Gaps
- **1 isolated node(s):** `multi-agent-conversational-orchestration`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 102 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `Community 5` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `run_guardrail_suite()` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `run_eval()` connect `Community 7` to `Community 0`, `Community 1`, `Community 5`, `Community 9`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `IncidentInput` (e.g. with `test_crewai_mock_offline()` and `test_genai_judge_and_regenerator_offline_doubles()`) actually correct?**
  _`IncidentInput` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Policy` (e.g. with `test_langgraph_graph_builds()` and `test_mongo_run_store_offline_double()`) actually correct?**
  _`Policy` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `FixtureJudge` (e.g. with `test_langgraph_graph_builds()` and `test_mongo_run_store_offline_double()`) actually correct?**
  _`FixtureJudge` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `FixtureRegenerator` (e.g. with `test_langgraph_graph_builds()` and `test_mongo_run_store_offline_double()`) actually correct?**
  _`FixtureRegenerator` has 11 INFERRED edges - model-reasoned connections that need verification._