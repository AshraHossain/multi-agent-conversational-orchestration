"""Offline-default CLI entrypoint for policy-gated incident triage."""

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from ma_co.core.models import IncidentInput, Policy
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run policy-gated incident triage CLI")
    parser.add_argument("--input", default="evaluation/datasets/incident.json")
    parser.add_argument("--live-crewai", action="store_true")
    args = parser.parse_args(argv)

    incident = IncidentInput.model_validate_json(
        Path(args.input).read_text(encoding="utf-8")
    )
    policy = Policy.model_validate_json(
        Path("policies/default.json").read_text(encoding="utf-8")
    )
    draft = f"Incident ID: {incident.incident_id}\nTriage: {incident.alert}. Cause unconfirmed."

    if args.live_crewai:
        if os.getenv("CREWAI_MOCK") != "1" and not os.getenv("BYNARA_API_KEY"):
            parser.error("Set BYNARA_API_KEY (or CREWAI_MOCK=1) for --live-crewai execution")
        from ma_co.adapters.crewai_incident import run_crew

        draft, reviewer_feedback = run_crew(
            incident,
            os.getenv("NARA_MODEL", "deepseek-v4-flash"),
        )
        print(json.dumps({"crew_reviewer_feedback": reviewer_feedback}))

    record = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy).run(
        incident,
        draft,
    )
    print(record.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
