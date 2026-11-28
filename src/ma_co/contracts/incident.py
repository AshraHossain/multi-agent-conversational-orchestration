"""Frozen domain contracts and schemas for policy-gated incident triage."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class Status(StrEnum):
    """Terminal and intermediate lifecycle states for an incident triage run."""

    PENDING = "pending"
    RUNNING = "running"
    APPROVED_DRAFT = "approved_draft"
    NEEDS_REVIEW = "needs_review"
    QUALITY_FAILED = "quality_failed"
    COST_EXCEEDED = "cost_exceeded"


class Policy(BaseModel):
    """Deterministic reflection and safety policy constraints."""

    model_config = ConfigDict(frozen=True)

    max_regenerations: int = Field(default=2, ge=0, le=5)
    min_score: float = Field(default=0.8, ge=0, le=1)
    max_estimated_cost_usd: float = Field(default=0.1, ge=0)
    forbidden_tools: frozenset[str] = Field(default_factory=frozenset)
    require_human_approval: bool = True


class IncidentInput(BaseModel):
    """Validated incident payload submitted for read-only triage."""

    model_config = ConfigDict(frozen=True)

    incident_id: str = Field(min_length=1, max_length=80)
    alert: str = Field(min_length=1, max_length=4000)
    evidence: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    proposed_action: str = Field(default="", max_length=400)


class FollowUpInput(BaseModel):
    """Validated operator follow-up payload for multi-turn incident triage."""

    model_config = ConfigDict(frozen=True)

    note: str = Field(min_length=1, max_length=2000)
    evidence: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    proposed_action: str | None = Field(default=None, max_length=400)


class JudgeResult(BaseModel):
    """Structured evaluation outcome from a Judge implementation."""

    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0, le=1)
    critique: str
    missing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    tool_use_valid: bool = True
    estimated_cost_usd: float = Field(default=0, ge=0)


class Iteration(BaseModel):
    """Immutable record of one evaluate/draft reflection iteration."""

    model_config = ConfigDict(frozen=True)

    number: int
    draft: str
    judge: JudgeResult
    at: datetime = Field(default_factory=utc_now)


class RunRecord(BaseModel):
    """Immutable persisted record of an incident triage run."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    incident: IncidentInput
    draft: str
    iterations: tuple[Iteration, ...] = Field(default_factory=tuple)
    status: Status = Status.QUALITY_FAILED
    improvement_delta: float = 0
    estimated_cost_usd: float = 0
    approved_by: str | None = None
    reviewed_by: str | None = None
    review_decision: str | None = None
    review_note: str = ""
    reviewed_at: datetime | None = None
    parent_run_id: str | None = None
    follow_up_note: str = ""
    reviewer_feedback: str = ""
    audit_digest: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RunListResponse(BaseModel):
    """Paginated response envelope for listing persisted runs."""

    model_config = ConfigDict(frozen=True)

    items: tuple[RunRecord, ...] = Field(default_factory=tuple)
    runs: tuple[RunRecord, ...] = Field(default_factory=tuple)
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class ApprovalInput(BaseModel):
    """Human reviewer decision payload for /v1/runs/{run_id}/review."""

    model_config = ConfigDict(frozen=True)

    approver: str = Field(min_length=2, max_length=100)
    decision: str
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def validate_decision(self) -> "ApprovalInput":
        if self.decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        return self


__all__ = [
    "ApprovalInput",
    "FollowUpInput",
    "IncidentInput",
    "Iteration",
    "JudgeResult",
    "Policy",
    "RunListResponse",
    "RunRecord",
    "Status",
    "utc_now",
]
