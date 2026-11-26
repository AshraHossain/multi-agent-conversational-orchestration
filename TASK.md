# Task Backlog — `ma_co`

Live engineering backlog tracked alongside [PLAN.md](PLAN.md) and [PLANNING.md](PLANNING.md).

## Done
- [x] Freeze all 6 Pydantic DTOs with `ConfigDict(frozen=True)` and immutable `tuple`/`frozenset` collections.
- [x] Implement defense-in-depth FastAPI middleware (`401` timing-safe auth, `429` sliding-window rate limit, `413` size cap, `415` MIME check, `400` path-traversal rejection, OWASP + telemetry headers).
- [x] Add `<untrusted_context>` XML boundary framing (`frame_untrusted_text`) and `sanitize_identifier`.
- [x] Add offline mock support (`CREWAI_MOCK=1`), LangGraph deterministic veto + pure fallback, `GenaiJudge`/`GenaiRegenerator`, and `MongoRunStore`.
- [x] Add multi-stage non-root `Dockerfile` (`UID 10001`), `docker-compose.yml`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and CI workflow.
- [x] Add dual Antigravity + Claude agent docs (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`) and `.claude/rules/` / `.claude/skills/`.
- [x] Phase 1: Add root `PLAN.md`, `TASK.md`, GSD → Superpowers → Ruflo `PLANNING.md`, `docs/adr/`, and `.claude/rules/contracts.md`.
- [x] Phase 2: Extract `src/ma_co/contracts/`, enable `branch = true` coverage, `W`/`SIM`/`RUF` Ruff rules, `ruff format --check`, and AST/layering/ground-truth/tool-allowlist guard tests (`tests/test_invariants.py`).
- [x] Phase 3: Upgrade `src/ma_co/eval.py` to 3-tier evaluation ladder (`--guardrails`, `--verifier-matrix`, `--repeat N`).
- [x] Phase 4: Update `README.md` (triad Mermaid diagrams + 3-tier scorecard), refresh `graphify-out/`, and pass `make check`.
- [x] Merge `feat/blueprint-parity-upgrade` into `main` (`--no-ff`), verify remote CI green, and tag `v0.2.0`.

## High Priority
- [ ] Run Tier-3 live evaluation (`--repeat 3`) and blind-spot replay (`paraphrased_certainty`, `subtle_causal_overclaim`) once live LLM budget is approved.

## Medium Priority
- [ ] Add live `--repeat 3` benchmark report against Gemini (`GOOGLE_API_KEY`) / Bynara (`BYNARA_API_KEY`) in `docs/eval_live_baseline.md` when cloud budget is approved.
- [ ] Add OpenTelemetry (`OTLP`) span export option behind an optional extra for distributed trace inspection.

## Low Priority
- [ ] Add async background triage worker option (`202 Accepted` + polling `/v1/runs/{run_id}`) for slow live multi-agent crews.
