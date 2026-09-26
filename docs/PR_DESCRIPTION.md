# Proposed community PR: bounded reflection contract
Motivation: agent handoffs need measurable failure modes, not just self-critique text.
Change: typed judge/regen interfaces, a deterministic LangGraph retry router, CrewAI read-only reviewer example, fixture tests, and policy-controlled action boundary.
Safety: no tool writes; approval recording is explicitly not action authorization. In production separate an authenticated execution service.
Validation: CI tests and ruff; no provider-backed performance claim.
Request: maintainers, please review the adapter seam, state schema, async strategy and recommendations for independent evaluation. Contributors can add new read-only adapters, evidence-backed judges, and calibrated benchmark datasets with tests.
