# ADR 0002: Deterministic Validation Veto Inside Bounded Reflection Loops

## Status
Accepted

## Context
LLM judges can occasionally award high scores to drafts that spoof or omit the input `incident_id` or contradict supplied telemetry evidence (e.g., claiming "no fixture evidence was available" when evidence exists).

## Decision
1. Run pure deterministic validation (`validate_incident_draft` via `apply_deterministic_veto`) after every `Judge.evaluate()` call in both `ReflectionEngine` and `langgraph_reflection.build_graph()`.
2. Any deterministic defect forces `score = 0.0` and appends concrete defect reasons to `missing_evidence` and `critique`, preventing premature approval.
3. Hard-bound retries (`Policy.max_regenerations`) and cost (`Policy.max_estimated_cost_usd`), failing closed to `Status.QUALITY_FAILED` or `Status.COST_EXCEEDED` and never auto-executing proposed actions.

## Consequences
- Hallucinated IDs and evidence contradictions cannot bypass the quality gate even with a permissive or mocked judge.
- Both the direct `ReflectionEngine` and LangGraph state machine share identical veto semantics.
