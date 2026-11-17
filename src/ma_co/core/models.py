from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class Status(str, Enum):
    APPROVED_DRAFT = "approved_draft"
    NEEDS_REVIEW = "needs_review"
    QUALITY_FAILED = "quality_failed"
    COST_EXCEEDED = "cost_exceeded"


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_regenerations: int = Field(default=2, ge=0, le=5)
    min_score: float = Field(default=0.8, ge=0, le=1)
    max_estimated_cost_usd: float = Field(default=0.1, ge=0)
    forbidden_tools: frozenset[str] = Field(default_factory=frozenset)
    require_human_approval: bool = True


class IncidentInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str = Field(min_length=1, max_length=80)
    alert: str = Field(min_length=1, max_length=4000)
    evidence: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    proposed_action: str = Field(default="", max_length=400)


class JudgeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0, le=1)
    critique: str
    missing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    tool_use_valid: bool = True
    estimated_cost_usd: float = Field(default=0, ge=0)


class Iteration(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    draft: str
    judge: JudgeResult
    at: datetime = Field(default_factory=utc_now)


class RunRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    incident: IncidentInput
    draft: str
    iterations: tuple[Iteration, ...] = Field(default_factory=tuple)
    status: Status = Status.QUALITY_FAILED
    improvement_delta: float = 0
    estimated_cost_usd: float = 0
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ApprovalInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    approver: str = Field(min_length=2, max_length=100)
    decision: str

    @model_validator(mode="after")
    def validate_decision(self) -> "ApprovalInput":
        if self.decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        return self
