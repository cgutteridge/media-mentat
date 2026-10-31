"""Evidence gate: pitch / refresh / clarify decisions and spoiler permission."""

from evidence_gate.gate import (
    HISTORICAL_AWARD_MAX_AGE_SECONDS,
    HISTORICAL_AWARD_SOFT_REUSE_SECONDS,
    LIVING_LIST_MAX_AGE_SECONDS,
    LIVING_LIST_SOFT_REUSE_SECONDS,
    ConsumptionCertainty,
    Decision,
    Finding,
    FindingKind,
    GateResult,
    evaluate,
)

__all__ = [
    "HISTORICAL_AWARD_MAX_AGE_SECONDS",
    "HISTORICAL_AWARD_SOFT_REUSE_SECONDS",
    "LIVING_LIST_MAX_AGE_SECONDS",
    "LIVING_LIST_SOFT_REUSE_SECONDS",
    "ConsumptionCertainty",
    "Decision",
    "Finding",
    "FindingKind",
    "GateResult",
    "evaluate",
]
