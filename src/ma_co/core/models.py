"""Compatibility re-export of frozen contracts from ma_co.contracts."""

from ma_co.contracts.incident import (
    ApprovalInput,
    IncidentInput,
    Iteration,
    JudgeResult,
    Policy,
    RunRecord,
    Status,
    utc_now,
)

__all__ = [
    "ApprovalInput",
    "IncidentInput",
    "Iteration",
    "JudgeResult",
    "Policy",
    "RunRecord",
    "Status",
    "utc_now",
]
