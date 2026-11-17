"""Reproducible offline evaluation harness. Outputs evaluation/eval_report.json."""
from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

from ma_co.core.models import IncidentInput, Policy, Status
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine

_DATASET = Path("evaluation/datasets/incident.json")


def _output_path() -> Path:
    base = Path(os.environ.get("EVAL_OUTPUT_DIR", "evaluation"))
    return base / "eval_report.json"


def run_eval(n_runs: int = 10) -> dict:
    incident = IncidentInput.model_validate_json(_DATASET.read_text(encoding="utf-8"))
    policy = Policy.model_validate_json(
        Path("policies/default.json").read_text(encoding="utf-8")
    )
    engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)

    final_scores: list[float] = []
    latencies_ms: list[float] = []
    grounded = 0
    guardrail_pass = 0

    for _ in range(n_runs):
        draft = f"Triage: {incident.alert}. Cause unconfirmed."
        t0 = time.perf_counter()
        record = engine.run(incident, draft)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

        last = record.iterations[-1] if record.iterations else None
        score = last.judge.score if last else 0.0
        final_scores.append(score)

        if incident.evidence and any(e[:20] in record.draft for e in incident.evidence):
            grounded += 1

        if record.status != Status.QUALITY_FAILED or len(record.iterations) > 1:
            guardrail_pass += 1

    sorted_ms = sorted(latencies_ms)
    report = {
        "n_runs": n_runs,
        "recall_at_1": round(statistics.mean(s >= 0.8 for s in final_scores), 4),
        "recall_at_3": round(statistics.mean(s >= 0.5 for s in final_scores), 4),
        "mean_final_score": round(statistics.mean(final_scores), 4),
        "grounding_rate": round(grounded / n_runs, 4),
        "guardrail_pass_rate": round(guardrail_pass / n_runs, 4),
        "latency_p50_ms": round(statistics.median(latencies_ms), 2),
        "latency_p95_ms": round(sorted_ms[max(0, int(0.95 * n_runs) - 1)], 2),
    }

    out = _output_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run_eval()
    for k, v in report.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
