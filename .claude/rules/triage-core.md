---
paths:
  - "src/ma_co/**/*.py"
---
# ma_co Core & Adapter Rules (`src/ma_co/`)
1. Keep `ma_co/core/` independent of FastAPI, CrewAI, and LangGraph imports.
2. Enforce bounded reflection rounds and policy checks in `ma_co/core/reflection.py`.
