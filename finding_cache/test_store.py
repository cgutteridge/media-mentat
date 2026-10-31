"""Behaviour tests for the Finding cache store seam."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import FindingKind, evaluate
from finding_cache.store import load_finding, to_gate_finding, write_finding

NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


def _living_list_record(*, finding_id: str, fetched_at: datetime) -> dict:
    return {
        "finding_id": finding_id,
        "kind": "living_list",
        "payload": {"award": "hugo", "year": 2024, "members": []},
        "source_refs": ["https://www.thehugoawards.org/hugo-history/2024-hugo-awards/"],
        "fetched_at": fetched_at.isoformat(),
        "max_age_seconds": 90 * 24 * 60 * 60,
        "swr_seconds": 7 * 24 * 60 * 60,
        "status": "active",
    }


def test_write_and_load_round_trip_preserves_schema_fields(tmp_path: Path) -> None:
    record = _living_list_record(finding_id="hugo-2024", fetched_at=NOW)

    write_finding(tmp_path, record)
    loaded = load_finding(tmp_path, "hugo-2024")

    assert loaded == record


def test_supersede_marks_previous_soft_stale_instead_of_deleting(
    tmp_path: Path,
) -> None:
    older = _living_list_record(
        finding_id="hugo-2024",
        fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    newer = _living_list_record(finding_id="hugo-2024", fetched_at=NOW)
    newer["payload"] = {
        "award": "hugo",
        "year": 2024,
        "members": [{"title": "Some Desperate Glory", "creator": "Emily Tesh"}],
    }

    write_finding(tmp_path, older)
    write_finding(tmp_path, newer)

    active = load_finding(tmp_path, "hugo-2024")
    assert active["status"] == "active"
    assert active["fetched_at"] == NOW.isoformat()
    assert len(active["payload"]["members"]) == 1

    soft_stale = [
        path
        for path in tmp_path.glob("hugo-2024*.json")
        if path.name != "hugo-2024.json"
    ]
    assert len(soft_stale) == 1
    archived = load_finding(tmp_path, soft_stale[0].stem)
    assert archived["status"] == "soft-stale"
    assert archived["fetched_at"] == older["fetched_at"]
    assert archived["payload"]["members"] == []


def test_loaded_finding_is_evaluable_by_evidence_gate(tmp_path: Path) -> None:
    record = _living_list_record(finding_id="hugo-2024", fetched_at=NOW)
    write_finding(tmp_path, record)

    gate_finding = to_gate_finding(load_finding(tmp_path, "hugo-2024"))
    result = evaluate(certainty={}, findings=(gate_finding,), now=NOW)

    assert gate_finding.kind is FindingKind.LIVING_LIST
    assert result.decision.value == "allow"
    assert result.refresh_suggested is False


def test_soft_stale_loaded_finding_suggests_refresh(tmp_path: Path) -> None:
    from datetime import timedelta

    soft_age = NOW - timedelta(days=93)
    record = _living_list_record(finding_id="hugo-2024", fetched_at=soft_age)
    write_finding(tmp_path, record)

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(load_finding(tmp_path, "hugo-2024")),),
        now=NOW,
    )
    assert result.decision.value == "allow"
    assert result.refresh_suggested is True
