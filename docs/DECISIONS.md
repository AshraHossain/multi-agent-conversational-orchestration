# Orchestration decisions

CrewAI `Process.sequential` runs Triager, Investigator and Safety Reviewer in order. `Task(context=[...])` makes handoffs explicit. Each role gets narrowly scoped access; only the first two get the read-only signal tool. The last task's result is a critique, not authority to act. The external reflection engine rechecks a candidate and returns a quality status. For real use, replace the deterministic fixture judge with independent evidence-grounded evaluation and calibrate with human labels.

LangGraph routing is deterministic: if cost exceeds cap, stop; if score passes and evidence/tool checks pass, stop; if retries exhausted, stop; otherwise regenerate and re-evaluate. If quality fails after the last retry, return `quality_failed` for human triage, never an auto-action. The graph implementation is an optional demonstration; do not invoke a framework agent again as a side effect of regeneration.

Choose a reusable reflection **subgraph** for most workflows: it provides explicit bounded state transitions and observability, and can be composed as a node of a larger graph. An edge interceptor may be useful for instrumentation but is a poor place to hide LLM calls, budget accounting or write approvals.

Keep only the latest draft, a concise bounded critique (e.g., 500 chars) and last three score/critique entries in graph state. Persist full critiques in an external trace store keyed by run ID and iteration. For retrieval, select evidence by source ID and token budget; never append every previous conversation message. In production use token counting and deterministic summaries validated against source IDs, not arbitrary truncation alone.
