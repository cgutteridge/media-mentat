"""Behaviour tests for the recommend pull (Evidence gate + medium members) seam."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recommend_pull.pull import (
    is_screen_category,
    is_short_fiction_category,
    recommend_pull,
)

NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_empty_cache_cannot_allow_recommendations(tmp_path: Path) -> None:
    record = tmp_path / "record.md"
    record.write_text(GRILLING)

    result = recommend_pull(cache_dir=tmp_path / "missing", grilling_record=record, now=NOW)

    assert result.decision == "clarify-or-refuse"
    assert result.members == ()

GRILLING = """\
# Taste record

## Consumption certainty

| Title | Creator | Certainty |
| --- | --- | --- |
| Example Novel C | Example Writer C | heard-of |
| Example Novel A | Example Writer A | consumed |
"""


def _write_living_list(
    cache_dir: Path,
    *,
    finding_id: str,
    members: list[dict],
    fetched_at: datetime = NOW,
) -> None:
    record = {
        "finding_id": finding_id,
        "kind": "living_list",
        "payload": {"award": "hugo", "year": 2024, "members": members},
        "source_refs": [
            "https://www.thehugoawards.org/hugo-history/2024-hugo-awards/",
        ],
        "fetched_at": fetched_at.isoformat(),
        "max_age_seconds": 90 * 24 * 60 * 60,
        "swr_seconds": 7 * 24 * 60 * 60,
        "status": "active",
    }
    (cache_dir / f"{finding_id}.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )


MIXED_MEMBERS = [
    {
        "title": "Example Novel C",
        "creator": "Example Writer C",
        "category": "Best Novel",
        "year": 2024,
    },
    {
        "title": "Example Novella",
        "creator": "Example Writer G",
        "category": "Best Novella",
        "year": 2024,
    },
    {
        "title": "Novelette Only",
        "creator": "Someone",
        "category": "Best Novelette",
        "year": 2024,
    },
    {
        "title": "Short Only",
        "creator": "Short Author",
        "category": "Best Short Story",
        "year": 2024,
    },
    {
        "title": "Example Feature",
        "creator": "Example Director",
        "category": "Best Dramatic Presentation, Long Form",
        "year": 2024,
    },
    {
        "title": "Example Episode",
        "creator": "Example Studio",
        "category": "Best Dramatic Presentation, Short Form",
        "year": 2024,
    },
    {
        "title": "Editor Person",
        "creator": "Editor Person",
        "category": "Best Editor Short Form",
        "year": 2024,
    },
]


def test_recommend_pull_allows_fresh_cache_and_lists_novel_novella_members(
    tmp_path: Path,
) -> None:
    """Gate-allow path: fresh findings + novel/novella members (not novelette)."""
    cache_dir = tmp_path / "findings"
    cache_dir.mkdir()
    grilling = tmp_path / "grilling-record.md"
    grilling.write_text(GRILLING, encoding="utf-8")

    _write_living_list(
        cache_dir,
        finding_id="hugo-2024",
        members=MIXED_MEMBERS,
    )
    # Soft-stale archive (same finding_id, stamped filename) must be ignored.
    archive = {
        "finding_id": "hugo-2024",
        "kind": "living_list",
        "payload": {
            "award": "hugo",
            "year": 2023,
            "members": [
                {
                    "title": "Archived Novel",
                    "creator": "Ghost",
                    "category": "Best Novel",
                    "year": 2023,
                },
            ],
        },
        "source_refs": ["https://example.test/archive"],
        "fetched_at": "2023-01-01T00:00:00+00:00",
        "max_age_seconds": 90 * 24 * 60 * 60,
        "swr_seconds": 7 * 24 * 60 * 60,
        "status": "soft-stale",
    }
    (
        cache_dir / "hugo-2024.2023-01-01T00-00-00p00-00.json"
    ).write_text(json.dumps(archive, indent=2) + "\n", encoding="utf-8")

    result = recommend_pull(
        cache_dir=cache_dir,
        grilling_record=grilling,
        now=NOW,
    )

    assert result.decision == "allow"
    assert result.refresh_suggested is False
    assert result.missing_required_finding_ids == ()
    assert result.blocked_finding_ids == ()
    assert result.finding_ids == ("hugo-2024",)
    assert result.medium == "books"

    titles = {m["title"] for m in result.members}
    assert titles == {"Example Novel C", "Example Novella"}
    assert all(m["finding_id"] == "hugo-2024" for m in result.members)
    assert all(m["medium"] == "books" for m in result.members)
    # Backward-compatible alias
    assert result.book_members == result.members


def test_recommend_pull_screen_lists_dramatic_presentation_only(
    tmp_path: Path,
) -> None:
    """Screen medium: Dramatic Presentation members only; books stay default."""
    cache_dir = tmp_path / "findings"
    cache_dir.mkdir()
    grilling = tmp_path / "grilling-record.md"
    grilling.write_text(GRILLING, encoding="utf-8")
    _write_living_list(cache_dir, finding_id="hugo-2024", members=MIXED_MEMBERS)

    result = recommend_pull(
        cache_dir=cache_dir,
        grilling_record=grilling,
        medium="screen",
        now=NOW,
    )

    assert result.medium == "screen"
    titles = {m["title"] for m in result.members}
    assert titles == {"Example Feature", "Example Episode"}
    by_title = {m["title"]: m for m in result.members}
    assert by_title["Example Feature"]["medium"] == "film"
    assert by_title["Example Episode"]["medium"] == "tv-episode"
    assert {m["category"] for m in result.members} == {
        "Best Dramatic Presentation, Long Form",
        "Best Dramatic Presentation, Short Form",
    }


def test_recommend_pull_short_lists_short_and_novelette_not_editor_or_dp(
    tmp_path: Path,
) -> None:
    """Short medium: short story / novelette; exclude editor and DP short form."""
    cache_dir = tmp_path / "findings"
    cache_dir.mkdir()
    grilling = tmp_path / "grilling-record.md"
    grilling.write_text(GRILLING, encoding="utf-8")
    _write_living_list(cache_dir, finding_id="hugo-2024", members=MIXED_MEMBERS)

    result = recommend_pull(
        cache_dir=cache_dir,
        grilling_record=grilling,
        medium="short",
        now=NOW,
    )

    assert result.medium == "short"
    titles = {m["title"] for m in result.members}
    assert titles == {"Novelette Only", "Short Only"}
    assert all(m["medium"] == "short" for m in result.members)


def test_format_pull_report_labels_medium_and_category(
    tmp_path: Path,
) -> None:
    """Report makes medium and category obvious per member."""
    from recommend_pull.pull import format_pull_report

    cache_dir = tmp_path / "findings"
    cache_dir.mkdir()
    grilling = tmp_path / "grilling-record.md"
    grilling.write_text(GRILLING, encoding="utf-8")
    _write_living_list(cache_dir, finding_id="hugo-2024", members=MIXED_MEMBERS)

    report = format_pull_report(
        recommend_pull(
            cache_dir=cache_dir,
            grilling_record=grilling,
            medium="screen",
            now=NOW,
        )
    )
    assert "medium: screen" in report
    assert "Best Dramatic Presentation, Long Form" in report
    assert "Example Feature" in report
    assert "[film]" in report
    assert "[tv-episode]" in report
    assert "Example Novel C" not in report


def test_screen_form_label_from_category() -> None:
    """Long/Short Form Hugo categories map to film vs tv-episode labels."""
    from recommend_pull.pull import screen_form_label

    assert screen_form_label("Best Dramatic Presentation, Long Form") == "film"
    assert screen_form_label("Best Dramatic Presentation, Short Form") == (
        "tv-episode"
    )
    assert screen_form_label("Outstanding Dramatic Presentation") == "screen"


def test_category_matchers_exclude_noise() -> None:
    """Category helpers refuse editor / DP short labels for short fiction."""
    assert is_screen_category("Best Dramatic Presentation, Long Form")
    assert is_screen_category("Ray Bradbury Nebula Award for Outstanding Dramatic Presentation")
    assert not is_screen_category("Best Novel")

    assert is_short_fiction_category("Best Short Story")
    assert is_short_fiction_category("SHORT STORIES")
    assert is_short_fiction_category("Best Novelette")
    assert is_short_fiction_category("shorter fiction")
    assert not is_short_fiction_category("Best Editor Short Form")
    assert not is_short_fiction_category("Best Dramatic Presentation, Short Form")
    assert not is_short_fiction_category("NON-FICTION")
    assert not is_short_fiction_category("Best Novel")
