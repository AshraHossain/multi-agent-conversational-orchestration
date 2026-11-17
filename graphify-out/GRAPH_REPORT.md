# Graph Report - multi-agent-conversational-orchestration  (2026-11-16)

## Corpus Check
- 42 files · ~8,648 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 247 nodes · 488 edges · 27 communities (14 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `27b2ab37`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- models.py
- test_reflection.py
- IncidentInput
- frame_untrusted_text
- crewai_incident.py
- Agent prompts (reviewed and versioned)
- Architecture and Component Contracts
- Multi-Agent Conversational Orchestration
- DECISIONS.md
- PLAN.md
- RunRecord
- multi-agent-conversational-orchestration
- test_api.py
- test_security.py
- test_store.py
- AGENTS.md — Multi-Agent Conversational Orchestration (`ma_co`)
- test_eval.py
- api-and-adapters.md
- tests-and-eval.md
- triage-core.md
- SKILL.md

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 39 edges
2. `RunRecord` - 18 edges
3. `ReflectionEngine` - 17 edges
4. `Policy` - 14 edges
5. `FixtureJudge` - 14 edges
6. `sanitize_identifier()` - 14 edges
7. `Status` - 13 edges
8. `run_eval()` - 13 edges
9. `JudgeResult` - 12 edges
10. `frame_untrusted_text()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_genai_judge_live()` --uses--> `GenaiJudge`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/genai_adapter.py
- `test_langgraph_graph_builds()` --calls--> `build_graph()`  [INFERRED]
  tests/test_adapters.py → src/ma_co/adapters/langgraph_reflection.py
- `test_cost_cap_stops_loop()` --uses--> `Status`  [INFERRED]
  tests/test_reflection.py → src/ma_co/core/models.py
- `test_no_proposed_action_gives_approved_draft()` --uses--> `Status`  [INFERRED]
  tests/test_reflection.py → src/ma_co/core/models.py
- `test_pass_to_needs_review()` --uses--> `Status`  [INFERRED]
  tests/test_reflection.py → src/ma_co/core/models.py

## Import Cycles
- None detected.

## Communities (27 total, 7 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.13
Nodes (30): BaseModel, datetime, Enum, get, middleware, model_validator, post, Request (+22 more)

### Community 1 - "test_reflection.py"
Cohesion: 0.32
Nodes (10): _engine(), unit, test_draft_missing_evidence_triggers_regen(), test_forbidden_tool_raises(), test_idempotent_draft_stops_loop(), test_improvement_delta_computed(), test_negative_cost_raises(), test_no_proposed_action_gives_approved_draft() (+2 more)

### Community 2 - "IncidentInput"
Cohesion: 0.11
Nodes (16): Protocol, GenaiJudge, GenaiRegenerator, google-genai live Judge and Regenerator. Requires GOOGLE_API_KEY and the…, Live Judge backed by google-generativeai. Falls back to fixture on import error., Live Regenerator backed by google-generativeai., build_graph(), Graph owns the bounded loop; action execution is deliberately outside the graph. (+8 more)

### Community 3 - "frame_untrusted_text"
Cohesion: 0.18
Nodes (7): frame_untrusted_text(), Wrap untrusted external content in XML data boundaries to block prompt…, Return factual/structural defects that must block the quality gate., validate_incident_draft(), unit, TestFrameUntrustedText, TestValidateIncidentDraft

### Community 4 - "crewai_incident.py"
Cohesion: 0.17
Nodes (13): live, _mock_run_crew(), Opt-in live 3-agent CrewAI crew. Requires provider credentials and extra…, Deterministic offline stand-in used when CREWAI_MOCK=1., run_crew(), read_incident_signal(), lookup_event(), Read-only fixture telemetry. Live connectors belong behind scoped service… (+5 more)

### Community 5 - "Agent prompts (reviewed and versioned)"
Cohesion: 0.33
Nodes (5): Agent prompts (reviewed and versioned), Investigator, Regenerator, Safety reviewer, Triager

### Community 6 - "Architecture and Component Contracts"
Cohesion: 0.25
Nodes (7): API, Architecture and Component Contracts, Component Boundaries, End-to-End Request Sequence, Invariants, Layered System Architecture, Tool Contracts

### Community 7 - "Multi-Agent Conversational Orchestration"
Cohesion: 0.12
Nodes (15): Architecture, Configuration, End-to-End Request Sequence, Evaluation Scorecard, Layered System Architecture, License, Module Layout, Multi-Agent Conversational Orchestration (+7 more)

### Community 10 - "RunRecord"
Cohesion: 0.14
Nodes (10): MongoRunStore, Optional MongoDB-backed RunStore. Requires pymongo and MONGO_URI env var., MongoDB-backed RunStore. Same interface as core.store.RunStore., RunRecord, Path, Small local dev store. Use durable DB + transactions for production., RunStore, Strip path-traversal and non-safe chars from an identifier (e.g. run_id,… (+2 more)

### Community 17 - "test_api.py"
Cohesion: 0.30
Nodes (14): unit, The review endpoint records a decision only — never performs the action., test_422_on_missing_fields(), test_get_run_bad_id_400(), test_get_run_not_found(), test_get_run_ok(), test_health_endpoints(), test_owasp_headers_present() (+6 more)

### Community 18 - "test_security.py"
Cohesion: 0.26
Nodes (11): unit, Security branch coverage: 401, 413, 415, 429, path traversal., test_missing_token_401(), test_no_auth_token_allows_all(), test_oversized_payload_413(), test_path_traversal_in_run_id_400(), test_probe_bypasses_auth(), test_rate_limit_429() (+3 more)

### Community 19 - "test_store.py"
Cohesion: 0.41
Nodes (11): unit, save() uses staging file so a crash mid-write can't leave a corrupt file., _record(), _store(), test_atomic_write(), test_get_invalid_uuid_format(), test_get_missing_returns_none(), test_invalid_uuid_rejected() (+3 more)

### Community 20 - "AGENTS.md — Multi-Agent Conversational Orchestration (`ma_co`)"
Cohesion: 0.20
Nodes (7): AGENTS.md — Multi-Agent Conversational Orchestration (`ma_co`), Module Layout, Repo-Specific Invariants, Verified Commands, What This Project Is, CLAUDE.md — Multi-Agent Conversational Orchestration (`ma_co`), GEMINI.md — Multi-Agent Conversational Orchestration (`ma_co`)

### Community 21 - "test_eval.py"
Cohesion: 0.43
Nodes (6): unit, Offline eval harness tests — no LLM calls, no network., test_eval_module_importable(), test_eval_produces_report(), test_eval_scores_in_range(), test_eval_writes_json()

## Knowledge Gaps
- **35 isolated node(s):** `multi-agent-conversational-orchestration`, ``ma_co` API & Adapter Rules (`src/ma_co/api/`, `src/ma_co/adapters/`)`, ``ma_co` Testing & Evaluation Rules (`tests/`, `src/ma_co/eval.py`)`, ``ma_co` Core & Tool Invariants (`src/ma_co/core/`, `src/ma_co/tools/`)`, `Incident Triage Smoke Test` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 86 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `IncidentInput` to `models.py`, `test_reflection.py`, `frame_untrusted_text`, `crewai_incident.py`, `RunRecord`, `test_store.py`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Why does `sanitize_identifier()` connect `RunRecord` to `models.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `RunRecord` connect `RunRecord` to `models.py`, `test_store.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `IncidentInput` (e.g. with `_mock_run_crew()` and `run_crew()`) actually correct?**
  _`IncidentInput` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `RunRecord` (e.g. with `MongoRunStore` and `get_run()`) actually correct?**
  _`RunRecord` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ReflectionEngine` (e.g. with `IncidentInput` and `Iteration`) actually correct?**
  _`ReflectionEngine` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Policy` (e.g. with `build_graph()` and `main()`) actually correct?**
  _`Policy` has 6 INFERRED edges - model-reasoned connections that need verification._