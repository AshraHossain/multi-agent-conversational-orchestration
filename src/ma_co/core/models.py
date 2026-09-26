from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class Status(str, Enum):
    APPROVED_DRAFT = "approved_draft"
    NEEDS_REVIEW = "needs_review"
    QUALITY_FAILED = "quality_failed"
    COST_EXCEEDED = "cost_exceeded"


class Policy(BaseModel):
    max_regenerations: int = Field(default=2, ge=0, le=5)
    min_score: float = Field(default=0.8, ge=0, le=1)
    max_estimated_cost_usd: float = Field(default=0.1, ge=0)
    forbidden_tools: set[str] = Field(default_factory=set)
    require_human_approval: bool = True


class IncidentInput(BaseModel):
    incident_id: str = Field(min_length=1, max_length=80)
    alert: str = Field(min_length=1, max_length=4000)
    evidence: list[str] = Field(default_factory=list, max_length=20)
    proposed_action: str = Field(default="", max_length=400)


class JudgeResult(BaseModel):
    score: float = Field(ge=0, le=1)
    critique: str
    missing_evidence: list[str] = Field(default_factory=list)
    tool_use_valid: bool = True
    estimated_cost_usd: float = Field(default=0, ge=0)


class Iteration(BaseModel):
    number: int
    draft: str
    judge: JudgeResult
    at: datetime = Field(default_factory=utc_now)


class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    incident: IncidentInput
    draft: str
    iterations: list[Iteration] = Field(default_factory=list)
    status: Status = Status.QUALITY_FAILED
    improvement_delta: float = 0
    estimated_cost_usd: float = 0
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ApprovalInput(BaseModel):
    approver: str = Field(min_length=2, max_length=100)
    decision: str
    @model_validator(mode="after")
    def validate_decision(self):
        if self.decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        return self
