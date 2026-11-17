"""Bounded reflection engine and deterministic offline fixture doubles."""

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
    """Protocol for evaluating an incident triage draft."""

    def evaluate(self, incident: IncidentInput, draft: str) -> JudgeResult: ...


class Regenerator(Protocol):
    """Protocol for revising a draft based on judge critique."""

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
            missing_evidence=() if has_source else ("Cite incident evidence",),
        )


class FixtureRegenerator:
    """Deterministic demo regenerator that injects missing ID and evidence markers."""

    def regenerate(
        self,
        incident: IncidentInput,
        draft: str,
        critique: str,
    ) -> tuple[str, float]:
        revised = draft

        # Add an omitted ID, but do not mask an explicitly incorrect ID.
        if incident.incident_id not in revised and "Incident ID:" not in revised:
            revised = f"Incident ID: {incident.incident_id}\n{revised}"

        evidence = incident.evidence[0] if incident.evidence else "not supplied"
        revised += (
            f"\nEvidence: {evidence}"
            "\nAction is only a proposal; require approval."
        )

        return revised, 0.0


def apply_deterministic_veto(
    incident: IncidentInput,
    draft: str,
    result: JudgeResult,
) -> JudgeResult:
    """Apply pure deterministic validation defects to a JudgeResult."""
    defects = validate_incident_draft(incident, draft)
    if not defects:
        return result
    return result.model_copy(
        update={
            "score": 0.0,
            "critique": (
                result.critique
                + "\nDeterministic validation failures: "
                + "; ".join(defects)
            ),
            "missing_evidence": (*result.missing_evidence, *defects),
        }
    )


class ReflectionEngine:
    """Immutable, bounded reflection loop with deterministic policy gates."""

    def __init__(
        self,
        judge: Judge,
        regenerator: Regenerator,
        policy: Policy,
    ):
        self.judge = judge
        self.regenerator = regenerator
        self.policy = policy

    def run(
        self,
        incident: IncidentInput,
        draft: str,
        used_tools: set[str] | frozenset[str] | None = None,
    ) -> RunRecord:
        if (used_tools or frozenset()) & self.policy.forbidden_tools:
            raise ValueError("Forbidden tool requested")

        current_draft = draft
        iterations: list[Iteration] = []
        total_cost = 0.0
        initial_score: float | None = None
        status = Status.QUALITY_FAILED
        improvement_delta = 0.0

        for number in range(self.policy.max_regenerations + 1):
            raw_result = self.judge.evaluate(incident, current_draft)
            result = apply_deterministic_veto(incident, current_draft, raw_result)

            total_cost += result.estimated_cost_usd
            iterations.append(
                Iteration(
                    number=number,
                    draft=current_draft,
                    judge=result,
                )
            )

            if initial_score is None:
                initial_score = result.score
            improvement_delta = round(result.score - initial_score, 4)

            if total_cost > self.policy.max_estimated_cost_usd:
                status = Status.COST_EXCEEDED
                break

            if (
                result.score >= self.policy.min_score
                and result.tool_use_valid
                and not result.missing_evidence
            ):
                status = (
                    Status.NEEDS_REVIEW
                    if incident.proposed_action and self.policy.require_human_approval
                    else Status.APPROVED_DRAFT
                )
                break

            if number == self.policy.max_regenerations:
                break

            candidate, estimated_cost = self.regenerator.regenerate(
                incident,
                current_draft,
                result.critique,
            )

            if estimated_cost < 0:
                raise ValueError("Negative cost")

            total_cost += estimated_cost
            if total_cost > self.policy.max_estimated_cost_usd:
                status = Status.COST_EXCEEDED
                break

            if candidate == current_draft:
                break

            current_draft = candidate

        return RunRecord(
            incident=incident,
            draft=current_draft,
            iterations=tuple(iterations),
            status=status,
            improvement_delta=improvement_delta,
            estimated_cost_usd=total_cost,
            updated_at=utc_now(),
        )
