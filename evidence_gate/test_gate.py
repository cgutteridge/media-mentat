"""Behaviour tests for the Evidence gate seam."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from evidence_gate.gate import Decision, Finding, FindingKind, evaluate

NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


def _living_list(finding_id: str, fetched_at: datetime) -> Finding:
    return Finding(
        finding_id=finding_id,
        kind=FindingKind.LIVING_LIST,
        fetched_at=fetched_at,
    )


def _award_fact(finding_id: str, fetched_at: datetime) -> Finding:
    return Finding(
        finding_id=finding_id,
        kind=FindingKind.DISCOVERABLE_FACT,
        fetched_at=fetched_at,
    )


def test_spoilers_allowed_only_for_consumed_and_wont_read() -> None:
    result = evaluate(
        certainty={
            "work-a": "consumed",
            "work-b": "won't-read",
            "work-c": "heard-of",
            "work-d": "unknown",
        },
        findings=(),
        candidate_work_ids=("work-a", "work-b", "work-c", "work-d", "work-e"),
        now=NOW,
    )

    assert result.spoiler_allowed == {
        "work-a": True,
        "work-b": True,
        "work-c": False,
        "work-d": False,
        "work-e": False,
    }


def test_fresh_living_list_allows_pitch() -> None:
    finding = _living_list("hugo-2026", NOW - timedelta(days=30))

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
    assert result.blocked_finding_ids == ()


def test_living_list_within_soft_reuse_allows_with_refresh_suggested() -> None:
    # Fresh for 90 days; soft reuse for 7 more → age 93 days is soft.
    finding = _living_list("hugo-2026", NOW - timedelta(days=93))

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is True
    assert result.blocked_finding_ids == ()


def test_living_list_past_soft_reuse_must_refresh() -> None:
    finding = _living_list("hugo-2026", NOW - timedelta(days=98))

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.MUST_REFRESH
    assert result.blocked_finding_ids == ("hugo-2026",)


def test_historical_award_fact_fresh_within_one_year() -> None:
    finding = _award_fact("hugo-2016-novel", NOW - timedelta(days=200))

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False


def test_historical_award_fact_soft_reuse_then_must_refresh() -> None:
    soft = _award_fact("hugo-2016-novel", NOW - timedelta(days=370))
    soft_result = evaluate(certainty={}, findings=(soft,), now=NOW)
    assert soft_result.decision is Decision.ALLOW
    assert soft_result.refresh_suggested is True

    blocked = _award_fact("hugo-2016-novel", NOW - timedelta(days=380))
    blocked_result = evaluate(certainty={}, findings=(blocked,), now=NOW)
    assert blocked_result.decision is Decision.MUST_REFRESH
    assert blocked_result.blocked_finding_ids == ("hugo-2016-novel",)


def test_stable_work_identity_ignores_ttl() -> None:
    finding = Finding(
        finding_id="example-work",
        kind=FindingKind.STABLE_WORK,
        fetched_at=NOW - timedelta(days=10_000),
        max_age_seconds=1,
        swr_seconds=1,
    )

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
    assert result.blocked_finding_ids == ()


def test_missing_required_findings_clarify_or_refuse() -> None:
    present = _living_list("hugo-2026", NOW - timedelta(days=10))

    result = evaluate(
        certainty={},
        findings=(present,),
        required_finding_ids=("hugo-2026", "nebula-2026"),
        now=NOW,
    )

    assert result.decision is Decision.CLARIFY_OR_REFUSE
    assert result.missing_required_finding_ids == ("nebula-2026",)


def test_validated_at_preferred_over_fetched_at_for_age() -> None:
    finding = Finding(
        finding_id="hugo-2026",
        kind=FindingKind.LIVING_LIST,
        fetched_at=NOW - timedelta(days=200),
        validated_at=NOW - timedelta(days=10),
    )

    result = evaluate(certainty={}, findings=(finding,), now=NOW)

    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
