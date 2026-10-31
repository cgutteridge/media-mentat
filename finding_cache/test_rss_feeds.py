"""Behaviour tests for Clarkesworld / Escape Pod RSS Living List refresh."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from finding_cache.rss_feeds import (
    parse_short_fiction_rss,
    refresh_clarkesworld,
    refresh_escape_pod,
)
from finding_cache.store import load_finding

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_clarkesworld_rss_skips_interview_and_strips_by_author() -> None:
    xml_text = (FIXTURES / "clarkesworld_feed_snippet.xml").read_text(
        encoding="utf-8"
    )
    members = parse_short_fiction_rss(
        xml_text, category="Clarkesworld Short Fiction"
    )
    titles = {m["title"] for m in members}
    assert titles == {"A Vintage Kind of Death", "Quiet Orbit"}
    vintage = next(m for m in members if m["title"] == "A Vintage Kind of Death")
    assert vintage["creator"] == "Alex T. Singer"
    assert vintage["year"] == 2026
    assert vintage["category"] == "Clarkesworld Short Fiction"
    assert set(vintage) <= {"title", "creator", "category", "year"}


def test_parse_escape_pod_rss_skips_editorial() -> None:
    xml_text = (FIXTURES / "escape_pod_feed_snippet.xml").read_text(
        encoding="utf-8"
    )
    members = parse_short_fiction_rss(
        xml_text, category="Escape Pod Short Fiction"
    )
    titles = {m["title"] for m in members}
    assert "Editorial: Welcome Back" not in titles
    assert "EP800: The Long Way Around" in titles
    salt = next(m for m in members if "Salt" in m["title"])
    assert salt["creator"] == "Mei Chen"
    assert salt["title"] == "EP799: Salt and Soft Light"


def test_refresh_clarkesworld_writes_finding(tmp_path: Path) -> None:
    xml_text = (FIXTURES / "clarkesworld_feed_snippet.xml").read_text(
        encoding="utf-8"
    )
    finding_id = refresh_clarkesworld(
        cache_dir=tmp_path,
        rss_text=xml_text,
        fetched_at=NOW,
    )
    assert finding_id == "clarkesworld-rss"
    record = load_finding(tmp_path, finding_id)
    assert record["kind"] == "living_list"
    assert record["status"] == "active"
    assert len(record["payload"]["members"]) == 2


def test_refresh_escape_pod_writes_finding(tmp_path: Path) -> None:
    xml_text = (FIXTURES / "escape_pod_feed_snippet.xml").read_text(
        encoding="utf-8"
    )
    finding_id = refresh_escape_pod(
        cache_dir=tmp_path,
        rss_text=xml_text,
        fetched_at=NOW,
    )
    assert finding_id == "escape-pod-rss"
    record = load_finding(tmp_path, finding_id)
    assert record["payload"]["award"] == "escape-pod"
    assert len(record["payload"]["members"]) == 2
