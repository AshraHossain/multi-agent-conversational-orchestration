from typing import Protocol

from .models import (
    IncidentInput,
    Iteration,
    JudgeResult,
    Policy,
    RunRecord,
    Status,
    utc_now,
)
from .validation import validate_incident_draft


class Judge(Protocol):
    def evaluate(self, incident: IncidentInput, draft: str) -> JudgeResult: ...


class Regenerator(Protocol):
    def regenerate(
        self,
        incident: IncidentInput,
        draft: str,
        critique: str,
    ) -> tuple[str, float]: ...


class FixtureJudge:
    """Deterministic demo only; this is NOT a groundedness evaluator."""

    def evaluate(self, incident: IncidentInput, draft: str) -> JudgeResult:
        has_source = bool(incident.evidence) and "Evidence:" in draft
        return JudgeResult(
            score=0.9 if has_source else 0.3,
            critique="OK" if has_source else "Cite supplied evidence",
            missing_evidence=tuple() if has_source else ("Cite incident evidence",),
        )


class FixtureRegenerator:
    def regenerate(
        self,
        incident: IncidentInput,
        draft: str,
        critique: str,
    ) -> tuple[str, float]:
        revised = draft

        if incident.incident_id not in revised and "Incident ID:" not in revised:
            revised = f"Incident ID: {incident.incident_id}\n{revised}"

        evidence = incident.evidence[0] if incident.evidence else "not supplied"
        revised += (
            f"\nEvidence: {evidence}"
            "\nAction is only a proposal; require approval."
        )

        return revised, 0.0


class ReflectionEngine:
    def __init__(self, judge: Judge, regenerator: Regenerator, policy: Policy) -> None:
        self.judge = judge
        self.regenerator = regenerator
        self.policy = policy

    def run(
        self,
        incident: IncidentInput,
        draft: str,
        used_tools: set[str] | None = None,
    ) -> RunRecord:
        if (used_tools or set()) & self.policy.forbidden_tools:
            raise ValueError("Forbidden tool requested")

        record = RunRecord(incident=incident, draft=draft)
        initial_score: float | None = None

        for number in range(self.policy.max_regenerations + 1):
            result = self.judge.evaluate(incident, record.draft)

            defects = validate_incident_draft(incident, record.draft)
            if defects:
                result = result.model_copy(
                    update={
                        "score": 0.0,
                        "critique": (
                            result.critique
                            + "\nDeterministic validation failures: "
                            + "; ".join(defects)
                        ),
                        "missing_evidence": tuple(result.missing_evidence) + tuple(defects),
                    }
                )

            new_cost = record.estimated_cost_usd + result.estimated_cost_usd
            new_iterations = tuple(record.iterations) + (
                Iteration(number=number, draft=record.draft, judge=result),
            )

            if initial_score is None:
                initial_score = result.score

            improvement_delta = round(result.score - initial_score, 4)

            if new_cost >= self.policy.max_estimated_cost_usd:
                record = record.model_copy(
                    update={
                        "status": Status.COST_EXCEEDED,
                        "estimated_cost_usd": new_cost,
                        "iterations": new_iterations,
                        "improvement_delta": improvement_delta,
                        "updated_at": utc_now(),
                    }
                )
                break

            passes = (
                result.score >= self.policy.min_score
                and result.tool_use_valid
                and not result.missing_evidence
            )

            if passes:
                status = (
                    Status.NEEDS_REVIEW
                    if incident.proposed_action and self.policy.require_human_approval
                    else Status.APPROVED_DRAFT
                )
                record = record.model_copy(
                    update={
                        "status": status,
                        "estimated_cost_usd": new_cost,
                        "iterations": new_iterations,
                        "improvement_delta": improvement_delta,
                        "updated_at": utc_now(),
                    }
                )
                break

            record = record.model_copy(
                update={
                    "estimated_cost_usd": new_cost,
                    "iterations": new_iterations,
                    "improvement_delta": improvement_delta,
                }
            )

            if number == self.policy.max_regenerations:
                record = record.model_copy(update={"updated_at": utc_now()})
                break

            candidate, regen_cost = self.regenerator.regenerate(
                incident, record.draft, result.critique
            )

            if regen_cost < 0:
                raise ValueError("Negative cost")

            new_cost2 = record.estimated_cost_usd + regen_cost
            if new_cost2 > self.policy.max_estimated_cost_usd:
                record = record.model_copy(
                    update={
                        "status": Status.COST_EXCEEDED,
                        "estimated_cost_usd": new_cost2,
                        "updated_at": utc_now(),
                    }
                )
                break

            if candidate == record.draft:
                record = record.model_copy(update={"updated_at": utc_now()})
                break

            record = record.model_copy(
                update={"draft": candidate, "estimated_cost_usd": new_cost2}
            )

        return record
