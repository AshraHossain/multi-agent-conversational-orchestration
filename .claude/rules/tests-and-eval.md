---
paths:
  - "tests/**/*.py"
  - "src/ma_co/eval.py"
---
# `ma_co` Testing & Evaluation Rules (`tests/`, `src/ma_co/eval.py`)
1. Default test runs (`uv run pytest`) must execute 100% offline with zero live network or LLM calls.
2. Categorize tests with `@pytest.mark.unit`, `@pytest.mark.integration`, and `@pytest.mark.live`.
3. Maintain >=95% line coverage across `src/ma_co/` (`--cov=ma_co --cov-fail-under=80`) and verify every HTTP status branch (`200`, `201`, `400`, `401`, `404`, `409`, `413`, `415`, `422`, `429`).
