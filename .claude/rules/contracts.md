---
paths:
  - "src/ma_co/contracts/**/*.py"
---
# `ma_co` Contracts Rules (`src/ma_co/contracts/`)
1. Every Pydantic model must set `model_config = ConfigDict(frozen=True)` and use immutable collection fields (`tuple`, `frozenset`).
2. Bound all external strings and collections with explicit `Field(min_length=..., max_length=...)` or numeric range constraints.
3. Never import FastAPI, CrewAI, LangGraph, Google GenAI, PyMongo, or `ma_co.core` / `ma_co.adapters` / `ma_co.api` inside `contracts/`.
