# ADR 0001: Strict Separation of `contracts/`, Pure `core/`, and `adapters/`

## Status
Accepted

## Context
Agentic systems tend to leak LLM SDK objects, web framework types, and mutable state across layers, making deterministic unit testing brittle and allowing accidental side effects inside business logic.

## Decision
1. Place all domain schemas (`Status`, `Policy`, `IncidentInput`, `JudgeResult`, `Iteration`, `RunRecord`, `ApprovalInput`) in `src/ma_co/contracts/` with `ConfigDict(frozen=True)` and immutable `tuple`/`frozenset` fields. Re-export them from `src/ma_co/core/models.py` for backward compatibility.
2. Keep `src/ma_co/core/` strictly free of `fastapi`, `crewai`, `langgraph`, `google.generativeai`, and `pymongo` imports.
3. Enforce this boundary automatically in `tests/test_invariants.py` using Python's `ast` module.

## Consequences
- Every core rule, validator, and reflection transition is 100% offline-testable in milliseconds.
- Adapters can be swapped (`FixtureJudge` ↔ `GenaiJudge`, `RunStore` ↔ `MongoRunStore`) without modifying core logic.
