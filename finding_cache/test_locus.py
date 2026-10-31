"""Behaviour tests for Locus awards and Recommended Reading refresh seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from evidence_gate.gate import Decision, evaluate
from finding_cache.locus import (
    parse_locus_html,
    refresh_locus,
    refresh_locus_rrl,
)
from finding_cache.store import load_finding, to_gate_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
AWARDS_SOURCE = (
    "https://locusmag.com/2026/04/2026-top-ten-finalists-for-locus-awards/"
)
RRL_SOURCE = "https://locusmag.com/2026/02/2025-recommended-reading/"


def test_parse_locus_awards_html_extracts_members() -> None:
    html = (FIXTURES / "locus_2026_awards_snippet.html").read_text(encoding="utf-8")

    payload = parse_locus_html(html, year=2026, award="locus")

    assert payload["award"] == "locus"
    assert payload["year"] == 2026
    assert {
        "title": "The Folded Sky",
        "creator": "Elizabeth Bear",
        "category": "SCIENCE FICTION NOVELS",
        "year": 2026,
    } in payload["members"]
    assert {
        "title": "The Devils",
        "creator": "Joe Abercrombie",
        "category": "FANTASY NOVELS",
        "year": 2026,
    } in payload["members"]
    assert {
        "title": "A Small Example",
        "creator": "Pat Author",
        "category": "NOVELLAS",
        "year": 2026,
    } in payload["members"]
    assert {
        "title": "Clarkesworld",
        "creator": "Clarkesworld",
        "category": "MAGAZINE",
        "year": 2026,
    } in payload["members"]
    assert {
        "title": "Neil Clarke",
        "creator": "Neil Clarke",
        "category": "EDITOR",
        "year": 2026,
    } in payload["members"]
    for m in payload["members"]:
        assert set(m) <= {"title", "creator", "category", "year", "medium"}


def test_parse_locus_rrl_html_extracts_members() -> None:
    html = (FIXTURES / "locus_rrl_2025_snippet.html").read_text(encoding="utf-8")

    payload = parse_locus_html(html, year=2025, award="locus-rrl")

    assert payload["award"] == "locus-rrl"
    assert payload["year"] == 2025
    assert {
        "title": "Sunward",
        "creator": "William Alexander",
        "category": "SCIENCE FICTION NOVELS",
        "year": 2025,
    } in payload["members"]
    assert {
        "title": "Dark Diamond",
        "creator": "Neal Asher",
        "category": "SCIENCE FICTION NOVELS",
        "year": 2025,
    } in payload["members"]
    # Work titles must not become categories even when they contain genre words.
    categories = {m["category"] for m in payload["members"]}
    assert not any("Icons of the Fantastic" in c for c in categories)
    assert {
        "title": (
            "Icons of the Fantastic: Illustrations of Imaginative "
            "Literature from the Korshak Collection"
        ),
        "creator": "George A. Vanderburgh",
        "category": "FANTASY NOVELS",
        "year": 2025,
    } in payload["members"]


def test_refresh_locus_writes_finding_evaluable_as_fresh(tmp_path: Path) -> None:
    html = (FIXTURES / "locus_2026_awards_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_locus(
        cache_dir=tmp_path,
        html=html,
        year=2026,
        source_url=AWARDS_SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "locus-2026"
    assert record["kind"] == "living_list"
    assert record["status"] == "active"
    assert AWARDS_SOURCE in record["source_refs"]
    assert len(record["payload"]["members"]) >= 3

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(record),),
        now=NOW,
    )
    assert result.decision is Decision.ALLOW
    assert result.refresh_suggested is False


def test_refresh_locus_rrl_writes_finding_evaluable_as_fresh(
    tmp_path: Path,
) -> None:
    html = (FIXTURES / "locus_rrl_2025_snippet.html").read_text(encoding="utf-8")

    finding_id = refresh_locus_rrl(
        cache_dir=tmp_path,
        html=html,
        year=2025,
        source_url=RRL_SOURCE,
        fetched_at=NOW,
    )

    record = load_finding(tmp_path, finding_id)
    assert record["finding_id"] == "locus-rrl-2025"
    assert record["kind"] == "living_list"
    assert record["payload"]["award"] == "locus-rrl"
    assert RRL_SOURCE in record["source_refs"]

    result = evaluate(
        certainty={},
        findings=(to_gate_finding(record),),
        now=NOW,
    )
    assert result.decision is Decision.ALLOW
