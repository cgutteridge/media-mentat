"""Behaviour tests for BSFA Living List HTML parse and refresh seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import Decision, evaluate
import pytest

from finding_cache.bsfa import parse_bsfa_html, refresh_bsfa
from finding_cache.store import load_finding, to_gate_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
SOURCE = "https://www.bsfa.co.uk/bsfa-awards-shortlist/"


def test_parse_bsfa_html_rejects_year_mismatch_with_page() -> None:
    html = (FIXTURES / "bsfa_2025_snippet.html").read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="published in 2025"):
        parse_bsfa_html(html, year=2019)


def test_parse_bsfa_html_extracts_table_title_author_members() -> None:
    html = (FIXTURES / "bsfa_2025_snippet.html").read_text(encoding="utf-8")

    payload = parse_bsfa_html(html, year=2025)

    assert payload["award"] == "bsfa"
    assert payload["year"] == 2025
    assert {
        "title": "The Salt Oracle",
        "creator": "Lorraine Wilson",
        "category": "Best Novel",
        "year": 2025,
    } in payload["members"]
    assert {
        "title": "Edge of Oblivion",
        "creator": "Kirk Weddell",
        "category": "Best Novel",
        "year": 2025,
    } in payload["members"]
    assert {
        "title": "A Clever Story",
        "creator": "Pat Writer",
        "category": "Best Short Fiction",
        "year": 2025,
    } in payload["members"]
    assert {
        "title": "Some Podcast",
        "creator": "Audio Person",
        "category": "Best Audio Fiction",
        "year": 2025,
    } in payload["members"]
    for member in payload["members"]:
        assert set(member) <= {"title", "creator", "category", "year", "medium"}
        assert member["title"] != "Title"
        assert member["creator"] != "Author"


def test_refresh_bsfa_writes_finding_evaluable_as_fresh(
    tmp_path: Path,
) -> None:
    html = (FIXTURES / "bsfa_2025_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_bsfa(
        cache_dir=tmp_path,
        html=html,
        year=2025,
        source_url=SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "bsfa-2025"
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
