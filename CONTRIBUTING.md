# Contributing

## Setup

```bash
git clone https://github.com/AshraHossain/multi-agent-conversational-orchestration
cd multi-agent-conversational-orchestration
uv sync --group dev
```

## Workflow

1. Branch from `main`: `git checkout -b feat/<topic>`
2. Write tests first (TDD) — `make test` must stay green
3. `make check` must pass before opening a PR
4. Conventional commit format: `feat|fix|docs|test|refactor|chore(scope): description`

## Gates (`make check`)

| Gate | Command | Threshold |
|------|---------|-----------|
| Lint | `ruff check .` | 0 errors |
| Tests + coverage | `pytest --cov=ma_co --cov-fail-under=80` | ≥80% |
| Eval | `python -m ma_co.eval` | offline, deterministic |

## Code conventions

- All Pydantic models `ConfigDict(frozen=True)`; mutations via `model_copy(update=…)`
- No mutating existing objects in core logic
- Security-sensitive paths (auth, rate-limit, sanitization) require a matching test in `tests/test_security.py`
- Live-network adapters (`genai_adapter.py`, `mongo_store.py`) must be gated with `@pytest.mark.live`

## PR checklist

- [ ] `make check` passes locally
- [ ] New behaviour has tests (unit or integration)
- [ ] Security-relevant change updated `SECURITY.md`
- [ ] `docs/ARCHITECTURE.md` updated if component boundaries changed
