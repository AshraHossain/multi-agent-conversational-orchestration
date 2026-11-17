# Contributing

1. Install dependencies with `make setup` (`uv sync --group dev`).
2. Follow TDD: write failing `@pytest.mark.unit` or `@pytest.mark.integration` tests before implementing changes.
3. Keep `src/ma_co/core/` pure and free of FastAPI, CrewAI, LangGraph, or network SDK imports.
4. Ensure all Pydantic models use `ConfigDict(frozen=True)` and state transitions return new instances via `model_copy(update=...)`.
5. Run `make check` (`uv run ruff check .`, `uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80`, `uv run python -m ma_co.eval`) before committing.
6. Use Conventional Commits (`feat|fix|test|refactor|docs|chore|perf|ci(scope): description`).
