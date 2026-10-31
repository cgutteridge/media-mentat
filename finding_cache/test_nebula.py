"""Behaviour tests for Nebula Living List HTML parse and refresh seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import Decision, evaluate
from finding_cache.nebula import parse_nebula_html, refresh_nebula
from finding_cache.store import load_finding, to_gate_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
SOURCE = "https://nebulas.sfwa.org/award-year/2024/"


def test_parse_nebula_html_extracts_title_creator_category_members() -> None:
    html = (FIXTURES / "nebula_2024_snippet.html").read_text(encoding="utf-8")

    payload = parse_nebula_html(html, year=2024)

    assert payload["award"] == "nebula"
    assert payload["year"] == 2024
    novels = [m for m in payload["members"] if m["category"] == "Best Novel"]
    assert {
        "title": "Sleeping Worlds Have No Memory",
        "creator": "Yaroslav Barsukov",
        "category": "Best Novel",
        "year": 2024,
    } in novels
    assert {
        "title": "Someone You Can Build a Nest In",
        "creator": "John Wiswell",
        "category": "Best Novel",
        "year": 2024,
    } in novels
    assert {
        "title": "The Tusks of Extinction",
        "creator": "Ray Nayler",
        "category": "Best Novella",
        "year": 2024,
    } in payload["members"]
    for member in payload["members"]:
        assert set(member) <= {"title", "creator", "category", "year", "medium"}


def test_refresh_nebula_writes_finding_evaluable_as_fresh(
    tmp_path: Path,
) -> None:
    html = (FIXTURES / "nebula_2024_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_nebula(
        cache_dir=tmp_path,
        html=html,
        year=2024,
        source_url=SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "nebula-2024"
    assert record["kind"] == "living_list"
    assert record["status"] == "active"
    assert SOURCE in record["source_refs"]
    assert len(record["payload"]["members"]) >= 4

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(record),),
        now=NOW,
    )
    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
