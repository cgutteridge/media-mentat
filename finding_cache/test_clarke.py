"""Behaviour tests for Clarke Living List HTML parse and refresh seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import Decision, evaluate
from finding_cache.clarke import parse_clarke_html, refresh_clarke
from finding_cache.store import load_finding, to_gate_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
SOURCE = "https://www.clarkeaward.com/"


def test_parse_clarke_html_extracts_year_shortlist_members() -> None:
    html = (FIXTURES / "clarke_2024_snippet.html").read_text(encoding="utf-8")

    payload = parse_clarke_html(html, year=2024)

    assert payload["award"] == "clarke"
    assert payload["year"] == 2024
    assert {
        "title": "In Ascension",
        "creator": "Martin MacInnes",
        "category": "Novel",
        "year": 2024,
    } in payload["members"]
    assert {
        "title": "Some Desperate Glory",
        "creator": "Emily Tesh",
        "category": "Novel",
        "year": 2024,
    } in payload["members"]
    assert {
        "title": "Chain-Gang All-Stars",
        "creator": "Nana Kwame Adjei-Brenyah",
        "category": "Novel",
        "year": 2024,
    } in payload["members"]
    assert {
        "title": "Also-Hyphenated Title",
        "creator": "A. Creator",
        "category": "Novel",
        "year": 2024,
    } in payload["members"]
    titles = {m["title"] for m in payload["members"]}
    assert "Venomous Lumpsucker" not in titles
    assert "Some Other Book" not in titles
    assert "Chain" not in titles
    assert len(payload["members"]) == 7
    for member in payload["members"]:
        assert set(member) <= {"title", "creator", "category", "year", "medium"}


def test_refresh_clarke_writes_finding_evaluable_as_fresh(
    tmp_path: Path,
) -> None:
    html = (FIXTURES / "clarke_2024_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_clarke(
        cache_dir=tmp_path,
        html=html,
        year=2024,
        source_url=SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "clarke-2024"
    assert record["kind"] == "living_list"
    assert record["status"] == "active"
    assert SOURCE in record["source_refs"]
    assert len(record["payload"]["members"]) == 7

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(record),),
        now=NOW,
    )
    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
