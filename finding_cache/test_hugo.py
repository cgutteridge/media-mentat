"""Behaviour tests for Hugo Living List HTML parse and refresh seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import Decision, evaluate
from finding_cache.hugo import parse_hugo_html, refresh_hugo
from finding_cache.store import load_finding, to_gate_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
SOURCE = "https://www.thehugoawards.org/hugo-history/2024-hugo-awards/"


def test_parse_hugo_html_extracts_title_creator_category_members() -> None:
    html = (FIXTURES / "hugo_2024_snippet.html").read_text(encoding="utf-8")

    payload = parse_hugo_html(html, year=2024)

    assert payload["award"] == "hugo"
    assert payload["year"] == 2024
    novels = [m for m in payload["members"] if m["category"] == "Best Novel"]
    assert {
        "title": "Some Desperate Glory",
        "creator": "Emily Tesh",
        "category": "Best Novel",
        "year": 2024,
    } in novels
    assert {
        "title": "Thornhedge",
        "creator": "T. Kingfisher",
        "category": "Best Novella",
        "year": 2024,
    } in payload["members"]
    translated = [
        m
        for m in payload["members"]
        if m["title"] == "Life Does Not Allow Us to Meet"
    ]
    assert translated == [
        {
            "title": "Life Does Not Allow Us to Meet",
            "creator": "He Xi",
            "category": "Best Novella",
            "year": 2024,
        }
    ]
    # Person-only categories: title equals the name; no invented plot fields.
    fan_writers = [
        m for m in payload["members"] if m["category"] == "Best Fan Writer"
    ]
    assert {"title": "Paul Weimer", "creator": "Paul Weimer", "category": "Best Fan Writer", "year": 2024} in fan_writers
    for member in payload["members"]:
        assert set(member) <= {"title", "creator", "category", "year", "medium"}


def test_refresh_hugo_writes_finding_evaluable_as_fresh(
    tmp_path: Path,
) -> None:
    html = (FIXTURES / "hugo_2024_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_hugo(
        cache_dir=tmp_path,
        html=html,
        year=2024,
        source_url=SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "hugo-2024"
    assert record["kind"] == "living_list"
    assert record["status"] == "active"
    assert SOURCE in record["source_refs"]
    assert len(record["payload"]["members"]) >= 5

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(record),),
        now=NOW,
    )
    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False
