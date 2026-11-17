# GEMINI.md — Multi-Agent Conversational Orchestration (`ma_co`)

Antigravity workspace entrypoint for `multi-agent-conversational-orchestration`.

- **Source of Truth**: Read and follow [AGENTS.md](AGENTS.md) for architecture, verified commands, module boundaries, and read-only incident triage invariants.
- **Scoped Rules**: Path-specific rules live in `.agents/rules/*.md` (symlinked to `.claude/rules/`).
- **Repo Skills**: Multi-step verification workflows live in `.agents/skills/*/SKILL.md` (symlinked to `.claude/skills/`).
- **Global Standards**: Inherits TDD, immutability, offline-first testing, dual Mermaid architecture diagrams, and OWASP security guardrails from `~/.gemini/config/plugins/gemini-core-workflow/`.
