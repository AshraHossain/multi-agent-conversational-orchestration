import argparse
import json
import os
from pathlib import Path

from ma_co.core.models import IncidentInput, Policy
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="evaluation/datasets/incident.json")
    parser.add_argument("--live-crewai", action="store_true")
    args = parser.parse_args()
    incident = IncidentInput.model_validate_json(Path(args.input).read_text(encoding="utf-8"))
    policy = Policy.model_validate_json(Path("policies/default.json").read_text(encoding="utf-8"))
    draft = f"Triage: {incident.alert}. Cause unconfirmed."
    if args.live_crewai:
        if not os.getenv("BYNARA_API_KEY"):
            parser.error("Set BYNARA_API_KEY for opt-in live CrewAI execution")
        from ma_co.adapters.crewai_incident import run_crew
        draft, reviewer_feedback = run_crew(incident, os.getenv("NARA_MODEL", "deepseek-v4-flash"))
        print(json.dumps({"crew_reviewer_feedback": reviewer_feedback}))
    record = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy).run(incident, draft)
    print(record.model_dump_json(indent=2))
    if args.live_crewai:
        if not os.getenv("BYNARA_API_KEY"):
            parser.error("Set BYNARA_API_KEY for live CrewAI execution")

        from ma_co.adapters.crewai_incident import run_crew

        draft, reviewer_feedback = run_crew(
            incident,
            os.getenv("NARA_MODEL", "deepseek-v4-flash"),
        )
        print(json.dumps({"crew_reviewer_feedback": reviewer_feedback}))
        

if __name__ == "__main__":
    main()
