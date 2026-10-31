"""Evidence gate module (test seam for freshness and Consumption certainty)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Sequence


class Decision(str, Enum):
    """Overall pitching decision for the evidence under evaluation."""

    ALLOW = "allow"
    MUST_REFRESH = "must-refresh"
    CLARIFY_OR_REFUSE = "clarify-or-refuse"


class FindingKind(str, Enum):
    """Kinds of Finding cache records the gate understands."""

    LIVING_LIST = "living_list"
    DISCOVERABLE_FACT = "discoverable_fact"
    STABLE_WORK = "stable_work"


# v1 freshness defaults (seconds). Applied when a Finding omits explicit ages.
# Soft-reuse window after max_age follows stale-while-revalidate (SWR) style.
_DAY = 24 * 60 * 60
LIVING_LIST_MAX_AGE_SECONDS = 90 * _DAY
LIVING_LIST_SOFT_REUSE_SECONDS = 7 * _DAY
HISTORICAL_AWARD_MAX_AGE_SECONDS = 365 * _DAY
HISTORICAL_AWARD_SOFT_REUSE_SECONDS = 14 * _DAY
# Back-compat aliases for private names used inside this module historically.
_LIVING_LIST_MAX_AGE_SECONDS = LIVING_LIST_MAX_AGE_SECONDS
_LIVING_LIST_SOFT_REUSE_SECONDS = LIVING_LIST_SOFT_REUSE_SECONDS
_HISTORICAL_AWARD_MAX_AGE_SECONDS = HISTORICAL_AWARD_MAX_AGE_SECONDS
_HISTORICAL_AWARD_SOFT_REUSE_SECONDS = HISTORICAL_AWARD_SOFT_REUSE_SECONDS


class ConsumptionCertainty(str, Enum):
    """Queryable per–Stable Work Consumption certainty values."""

    CONSUMED = "consumed"
    HEARD_OF = "heard-of"
    UNKNOWN = "unknown"
    WONT_READ = "won't-read"


_SPOILER_OK = frozenset(
    {ConsumptionCertainty.CONSUMED, ConsumptionCertainty.WONT_READ}
)


class _AgeBucket(str, Enum):
    FRESH = "fresh"
    SOFT = "soft"
    BLOCKED = "blocked"
    IGNORE = "ignore"


@dataclass(frozen=True)
class Finding:
    """A Finding cache record as seen by the Evidence gate.

    Attributes:
        finding_id: Stable id for this finding.
        kind: living_list, discoverable_fact, or stable_work.
        fetched_at: When the finding was fetched (UTC-aware preferred).
        validated_at: Optional later validation time; preferred over fetched_at
            for age when present.
        max_age_seconds: Optional override for fresh window; kind default if None.
        swr_seconds: Optional soft-reuse window after max_age (stale-while-
            revalidate); kind default if None.
        status: Cache status from the Finding cache schema (not used in v1
            age arithmetic).
    """

    finding_id: str
    kind: FindingKind
    fetched_at: datetime
    validated_at: datetime | None = None
    max_age_seconds: int | None = None
    swr_seconds: int | None = None
    status: str = "active"


@dataclass(frozen=True)
class GateResult:
    """Outcome of an Evidence gate evaluation.

    Attributes:
        decision: Whether pitching may proceed, must refresh, or clarify/refuse.
        refresh_suggested: True when pitching is allowed but a Research pass
            is advised (soft-reuse window).
        spoiler_allowed: Per Stable Work id whether spoilers are permitted.
        missing_required_finding_ids: Required ids absent from ``findings``.
        blocked_finding_ids: Findings past soft-reuse that must not be pitched from.
    """

    decision: Decision
    refresh_suggested: bool
    spoiler_allowed: Mapping[str, bool]
    missing_required_finding_ids: tuple[str, ...]
    blocked_finding_ids: tuple[str, ...]


def evaluate(
    *,
    certainty: Mapping[str, str | ConsumptionCertainty],
    findings: Sequence[Finding],
    required_finding_ids: Sequence[str] = (),
    candidate_work_ids: Sequence[str] = (),
    now: datetime | None = None,
) -> GateResult:
    """Decide pitch / refresh / clarify and spoiler permission from evidence.

    Args:
        certainty: Consumption certainty keyed by Stable Work id. Values should
            be ``consumed``, ``heard-of``, ``unknown``, or ``won't-read``.
            Missing candidates are treated as ``unknown``.
        findings: Finding records with timestamps and kinds.
        required_finding_ids: Finding ids that must be present or the gate
            returns clarify-or-refuse.
        candidate_work_ids: Stable Work ids to include in ``spoiler_allowed``.
            Combined with keys from ``certainty``.
        now: Evaluation instant (defaults to UTC now). Prefer injecting in tests.

    Returns:
        A :class:`GateResult` with aggregate decision and per-work spoiler map.
    """
    instant = now if now is not None else datetime.now(timezone.utc)
    spoiler_allowed = _spoiler_map(certainty, candidate_work_ids)

    present_ids = {f.finding_id for f in findings}
    missing = tuple(
        fid for fid in required_finding_ids if fid not in present_ids
    )
    if missing:
        return GateResult(
            decision=Decision.CLARIFY_OR_REFUSE,
            refresh_suggested=False,
            spoiler_allowed=spoiler_allowed,
            missing_required_finding_ids=missing,
            blocked_finding_ids=(),
        )

    blocked: list[str] = []
    soft: list[str] = []
    for finding in findings:
        bucket = _age_bucket(finding, instant)
        if bucket is _AgeBucket.BLOCKED:
            blocked.append(finding.finding_id)
        elif bucket is _AgeBucket.SOFT:
            soft.append(finding.finding_id)

    if blocked:
        return GateResult(
            decision=Decision.MUST_REFRESH,
            refresh_suggested=False,
            spoiler_allowed=spoiler_allowed,
            missing_required_finding_ids=(),
            blocked_finding_ids=tuple(blocked),
        )

    return GateResult(
        decision=Decision.ALLOW,
        refresh_suggested=bool(soft),
        spoiler_allowed=spoiler_allowed,
        missing_required_finding_ids=(),
        blocked_finding_ids=(),
    )


def _normalize_certainty(value: str | ConsumptionCertainty) -> ConsumptionCertainty:
    if isinstance(value, ConsumptionCertainty):
        return value
    try:
        return ConsumptionCertainty(value)
    except ValueError:
        return ConsumptionCertainty.UNKNOWN


def _spoiler_map(
    certainty: Mapping[str, str | ConsumptionCertainty],
    candidate_work_ids: Sequence[str],
) -> dict[str, bool]:
    work_ids = set(certainty) | set(candidate_work_ids)
    return {
        work_id: _normalize_certainty(
            certainty.get(work_id, ConsumptionCertainty.UNKNOWN)
        )
        in _SPOILER_OK
        for work_id in sorted(work_ids)
    }


def _age_bucket(finding: Finding, now: datetime) -> _AgeBucket:
    """Classify a finding's age relative to its freshness windows."""
    if finding.kind is FindingKind.STABLE_WORK:
        return _AgeBucket.IGNORE

    max_age, soft_reuse = _freshness_windows(finding)
    stamped = (
        finding.validated_at
        if finding.validated_at is not None
        else finding.fetched_at
    )
    age_seconds = (now - stamped).total_seconds()
    if age_seconds <= max_age:
        return _AgeBucket.FRESH
    if age_seconds <= max_age + soft_reuse:
        return _AgeBucket.SOFT
    return _AgeBucket.BLOCKED


def _freshness_windows(finding: Finding) -> tuple[int, int]:
    if finding.kind is FindingKind.LIVING_LIST:
        default_max = _LIVING_LIST_MAX_AGE_SECONDS
        default_soft = _LIVING_LIST_SOFT_REUSE_SECONDS
    else:
        # discoverable_fact — v1 default is historical-award lifetimes
        default_max = _HISTORICAL_AWARD_MAX_AGE_SECONDS
        default_soft = _HISTORICAL_AWARD_SOFT_REUSE_SECONDS

    max_age = (
        finding.max_age_seconds
        if finding.max_age_seconds is not None
        else default_max
    )
    soft_reuse = (
        finding.swr_seconds if finding.swr_seconds is not None else default_soft
    )
    return max_age, soft_reuse
