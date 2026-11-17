# Graph Report - multi-agent-conversational-orchestration  (2026-11-16)

## Corpus Check
- 9 files · ~5,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 281 nodes · 610 edges · 19 communities (13 shown, 2 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 115 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Domain Models & DTOs
- CLI & Policy Engine
- GenAI Adapters & Live Tests
- CI/CD & DevOps Config
- CrewAI Incident Adapter
- API Tests & Fixtures
- Validation & Eval Harness
- LangGraph Reflection Graph
- Adapter Unit Tests
- Security Tests
- FastAPI Middleware & Auth
- Store Tests
- Run Store
- Dependency Updates
- Package Metadata

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 48 edges
2. `Policy` - 21 edges
3. `RunRecord` - 20 edges
4. `ReflectionEngine` - 20 edges
5. `FixtureJudge` - 18 edges
6. `FixtureRegenerator` - 16 edges
7. `Status` - 15 edges
8. `JudgeResult` - 14 edges
9. `build_graph()` - 14 edges
10. `test_mongo_run_store_offline_double()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `EvalReport (3 cases)` --rationale_for--> `CI verify job (ruff + mypy + pytest + eval)`  [INFERRED]
  evaluation/eval_report.json → .github/workflows/ci.yml
- `pyproject.toml project config` --rationale_for--> `FastAPI app (Multi-Agent Incident Cockpit)`  [INFERRED]
  pyproject.toml → src/ma_co/api/main.py
- `FastAPI app (Multi-Agent Incident Cockpit)` --references--> `docker-compose ma-co service`  [INFERRED]
  src/ma_co/api/main.py → docker-compose.yml
- `FastAPI app (Multi-Agent Incident Cockpit)` --references--> `CI verify job (ruff + mypy + pytest + eval)`  [INFERRED]
  src/ma_co/api/main.py → .github/workflows/ci.yml
- `pull_request_template (make check gate)` --semantically_similar_to--> `CONTRIBUTING.md workflow + gates`  [INFERRED] [semantically similar]
  .github/pull_request_template.md → CONTRIBUTING.md

## Import Cycles
- None detected.

## Communities (19 total, 2 thin omitted)

### Community 0 - "Domain Models & DTOs"
Cohesion: 0.06
Nodes (41): ApprovalInput, BaseModel, datetime, get, IncidentInput, model_validator, post, RunRecord (+33 more)

### Community 1 - "CLI & Policy Engine"
Cohesion: 0.14
Nodes (30): main(), Offline-default CLI entrypoint for policy-gated incident triage., Policy, Terminal and intermediate lifecycle states for an incident triage run., Deterministic reflection and safety policy constraints., Status, FixtureJudge, FixtureRegenerator (+22 more)

### Community 2 - "GenAI Adapters & Live Tests"
Cohesion: 0.09
Nodes (19): live, Protocol, GenaiJudge, GenaiRegenerator, Live Judge backed by google-generativeai. Falls back to fixture on import error., Live Regenerator backed by google-generativeai., IncidentInput, JudgeResult (+11 more)

### Community 3 - "CI/CD & DevOps Config"
Cohesion: 0.11
Nodes (20): CI docker build job, CI verify job (ruff + mypy + pytest + eval), CONTRIBUTING.md workflow + gates, docker-compose ma-co service, EvalReport (3 cases), _JsonFormatter (structured JSON logs), LogRecord, FastAPI app (Multi-Agent Incident Cockpit) (+12 more)

### Community 4 - "CrewAI Incident Adapter"
Cohesion: 0.17
Nodes (19): Opt-in 3-agent CrewAI adapter with CREWAI_MOCK=1 offline fallback., Run the sequential Triager -> Investigator -> Safety Reviewer crew., run_crew(), read_incident_signal(), _run_mock_crew(), Return factual/structural defects that must block the quality gate., validate_incident_draft(), lookup_event() (+11 more)

### Community 5 - "API Tests & Fixtures"
Cohesion: 0.17
Nodes (17): CaptureFixture, fixture, Clear sliding-window rate limiter state (intended for test isolation)., Clear sliding-window rate limiter state (intended for test isolation)., reset_rate_limiter(), _clean_env_and_rate_limiter(), integration, MonkeyPatch (+9 more)

### Community 6 - "Validation & Eval Harness"
Cohesion: 0.18
Nodes (15): frame_untrusted_text(), Neutralize XML boundary-escape tags and wrap untrusted text as passive data., EvalCase, main(), Path, Deterministic evaluation & latency benchmark harness for ma_co. Run via: uv run…, Immutable specification of a single incident triage benchmark case., Execute the offline golden evaluation suite and return a structured scorecard. (+7 more)

### Community 7 - "LangGraph Reflection Graph"
Cohesion: 0.15
Nodes (9): build_graph(), evaluate(), _FallbackGraph, Pure-Python fallback when langgraph is not installed., Build a bounded reflection state machine using LangGraph or pure fallback., State, apply_deterministic_veto(), Apply pure deterministic validation defects to a JudgeResult. (+1 more)

### Community 8 - "Adapter Unit Tests"
Cohesion: 0.19
Nodes (6): unit, Offline and live-marked tests for CrewAI, LangGraph, GenAI, and MongoDB…, test_crewai_mock_offline(), test_genai_judge_and_regenerator_offline_doubles(), test_langgraph_graph_builds(), test_mongo_run_store_offline_double()

### Community 9 - "Security Tests"
Cohesion: 0.26
Nodes (11): unit, Security branch coverage: 401, 413, 415, 429, path traversal., test_missing_token_401(), test_no_auth_token_allows_all(), test_oversized_payload_413(), test_path_traversal_in_run_id_400(), test_probe_bypasses_auth(), test_rate_limit_429() (+3 more)

### Community 10 - "FastAPI Middleware & Auth"
Cohesion: 0.21
Nodes (12): Any, middleware, Request, Response, _attach_security_headers(), _check_rate_limit(), _extract_token(), Enforce auth, rate limiting, MIME/size caps, and OWASP security headers. (+4 more)

### Community 11 - "Store Tests"
Cohesion: 0.41
Nodes (11): unit, save() uses staging file so a crash mid-write can't leave a corrupt file., _record(), _store(), test_atomic_write(), test_get_invalid_uuid_format(), test_get_missing_returns_none(), test_invalid_uuid_rejected() (+3 more)

### Community 12 - "Run Store"
Cohesion: 0.43
Nodes (3): Path, Small local dev store. Use durable DB + transactions for production., RunStore

## Knowledge Gaps
- **7 isolated node(s):** `multi-agent-conversational-orchestration`, `pyproject.toml project config`, `_check_rate_limit (sliding-window)`, `_attach_security_headers (OWASP)`, `_JsonFormatter (structured JSON logs)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `GenAI Adapters & Live Tests` to `Domain Models & DTOs`, `CLI & Policy Engine`, `CrewAI Incident Adapter`, `Validation & Eval Harness`, `LangGraph Reflection Graph`, `Adapter Unit Tests`, `Store Tests`?**
  _High betweenness centrality (0.276) - this node is a cross-community bridge._
- **Why does `configure_logging()` connect `CI/CD & DevOps Config` to `Domain Models & DTOs`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `IncidentInput` (e.g. with `GenaiJudge` and `GenaiRegenerator`) actually correct?**
  _`IncidentInput` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Policy` (e.g. with `build_graph()` and `main()`) actually correct?**
  _`Policy` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RunRecord` (e.g. with `MongoRunStore` and `get_run()`) actually correct?**
  _`RunRecord` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ReflectionEngine` (e.g. with `IncidentInput` and `Policy`) actually correct?**
  _`ReflectionEngine` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `FixtureJudge` (e.g. with `IncidentInput` and `JudgeResult`) actually correct?**
  _`FixtureJudge` has 12 INFERRED edges - model-reasoned connections that need verification._