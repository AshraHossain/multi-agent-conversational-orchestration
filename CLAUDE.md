# CLAUDE.md — Multi-Agent Conversational Orchestration (`ma_co`)

Read [AGENTS.md](AGENTS.md) for project overview, verified commands, module layout, and core invariants.

- **Path-Scoped Rules**: `.claude/rules/` (symlinked from `.agents/rules/`)
- **Repo Skills**: `.claude/skills/` (symlinked from `.agents/skills/`)
- **Verification Gate**: Run `make check` (`ruff check .` + `pytest --cov` + `python -m ma_co.eval`) before completing any task.
