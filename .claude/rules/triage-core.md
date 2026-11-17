---
paths:
  - "src/ma_co/core/**/*.py"
  - "src/ma_co/tools/**/*.py"
---
# `ma_co` Core & Tool Invariants (`src/ma_co/core/`, `src/ma_co/tools/`)
1. Keep `ma_co/core/` and `ma_co/tools/` pure and independent of FastAPI, CrewAI, and LangGraph imports.
2. All Pydantic models in `models.py` must use `model_config = ConfigDict(frozen=True)`; never mutate models in-place.
3. Enforce deterministic draft validation (`validate_incident_draft`), path-safe identifier sanitization (`sanitize_identifier`), and `<untrusted_context>` prompt-injection framing (`frame_untrusted_text`) in `validation.py`.
4. Enforce bounded reflection rounds, cost caps, and forbidden-tool checks in `reflection.py`.
