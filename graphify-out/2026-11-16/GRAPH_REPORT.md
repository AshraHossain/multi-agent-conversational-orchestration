# Graph Report - multi-agent-conversational-orchestration  (2026-09-25)

## Corpus Check
- 26 files · ~3,088 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 102 nodes · 219 edges · 17 communities (8 shown, 4 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2f530eae`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- models.py
- IncidentInput
- reflection.py
- validate_incident_draft
- crewai_incident.py
- Agent prompts (reviewed and versioned)
- Architecture and component contracts
- Multi-agent conversational orchestration
- DECISIONS.md
- PLAN.md
- PR_DESCRIPTION.md
- multi-agent-conversational-orchestration

## God Nodes (most connected - your core abstractions)
1. `IncidentInput` - 25 edges
2. `Policy` - 14 edges
3. `ReflectionEngine` - 14 edges
4. `RunRecord` - 13 edges
5. `FixtureJudge` - 12 edges
6. `build_graph()` - 10 edges
7. `Status` - 10 edges
8. `FixtureRegenerator` - 10 edges
9. `Judge` - 8 edges
10. `review()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `test_bounded_failure()` --uses--> `Status`  [INFERRED]
  tests/test_reflection.py → src/ma_co/core/models.py
- `test_reflects_and_requests_review()` --uses--> `Status`  [INFERRED]
  tests/test_reflection.py → src/ma_co/core/models.py
- `test_evidence_marker_cannot_override_defects()` --uses--> `Status`  [INFERRED]
  tests/test_validation.py → src/ma_co/core/models.py
- `test_evidence_marker_cannot_override_defects()` --uses--> `Policy`  [INFERRED]
  tests/test_validation.py → src/ma_co/core/models.py
- `test_evidence_marker_cannot_override_defects()` --uses--> `FixtureJudge`  [INFERRED]
  tests/test_validation.py → src/ma_co/core/reflection.py

## Import Cycles
- None detected.

## Communities (17 total, 4 thin omitted)

### Community 0 - "models.py"
Cohesion: 0.15
Nodes (16): datetime, Enum, get, model_validator, post, get_run(), healthz(), review() (+8 more)

### Community 1 - "IncidentInput"
Cohesion: 0.27
Nodes (14): BaseModel, main(), IncidentInput, Iteration, JudgeResult, Policy, FixtureJudge, FixtureRegenerator (+6 more)

### Community 2 - "reflection.py"
Cohesion: 0.19
Nodes (7): Protocol, build_graph(), Graph owns the bounded loop; action execution is deliberately outside the graph., State, Judge, Regenerator, TypedDict

### Community 3 - "validate_incident_draft"
Cohesion: 0.43
Nodes (6): Return factual/structural defects that must block the quality gate., validate_incident_draft(), sample_incident(), test_evidence_marker_cannot_override_defects(), test_rejects_changed_incident_id(), test_rejects_evidence_contradiction()

### Community 4 - "crewai_incident.py"
Cohesion: 0.43
Nodes (5): Opt-in live 3-agent CrewAI crew. Requires provider credentials and extra…, run_crew(), read_incident_signal(), lookup_event(), Read-only fixture inputs. Live tools belong behind scoped service credentials.

### Community 5 - "Agent prompts (reviewed and versioned)"
Cohesion: 0.33
Nodes (5): Agent prompts (reviewed and versioned), Investigator, Regenerator, Safety reviewer, Triager

### Community 6 - "Architecture and component contracts"
Cohesion: 0.40
Nodes (4): API, Architecture and component contracts, Component boundaries, Tool contracts

### Community 7 - "Multi-agent conversational orchestration"
Cohesion: 0.50
Nodes (3): Multi-agent conversational orchestration, Security boundary, Setup (existing empty repo)

## Knowledge Gaps
- **13 isolated node(s):** `multi-agent-conversational-orchestration`, `Setup (existing empty repo)`, `Security boundary`, `Component boundaries`, `API` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 39 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `IncidentInput` connect `IncidentInput` to `models.py`, `reflection.py`, `validate_incident_draft`, `crewai_incident.py`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `build_graph()` connect `reflection.py` to `IncidentInput`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `RunRecord` connect `models.py` to `IncidentInput`, `reflection.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `IncidentInput` (e.g. with `run_crew()` and `build_graph()`) actually correct?**
  _`IncidentInput` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Policy` (e.g. with `build_graph()` and `main()`) actually correct?**
  _`Policy` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ReflectionEngine` (e.g. with `IncidentInput` and `Iteration`) actually correct?**
  _`ReflectionEngine` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `RunRecord` (e.g. with `get_run()` and `review()`) actually correct?**
  _`RunRecord` has 5 INFERRED edges - model-reasoned connections that need verification._