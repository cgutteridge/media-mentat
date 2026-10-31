"""Locus Awards and Recommended Reading Living List parse and refresh."""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

from finding_cache.living_list import (
    fetch_html,
    member,
    write_living_list_finding,
)

AwardSlug = Literal["locus", "locus-rrl"]

_TITLE_CREATOR = re.compile(
    r"^(?P<title>.+?),\s*(?P<creator>.+?)(?:\s*\([^)]*\))?\s*$"
)
_CATEGORY_HINT = re.compile(
    r"\b(NOVELS?|NOVELLAS|NOVELETTES|SHORT STORIES|ANTHOLOG(?:Y|IES)?|"
    r"COLLECTIONS?|MAGAZINE|PUBLISHER|EDITOR|ARTIST|ILLUSTRATED|"
    r"NON-FICTION|FIRST NOVEL|TRANSLATED|YOUNG ADULT|HORROR|FANTASY|"
    r"SCIENCE FICTION)\b",
    re.IGNORECASE,
)
_PROSE_NOISE = re.compile(
    r"congratulat|please email|links are purchase",
    re.IGNORECASE,
)


class _LocusListParser(HTMLParser):
    """Extract strong category headings and Title, Creator list items."""

    def __init__(self) -> None:
        super().__init__()
        self._in_strong = False
        self._in_li = False
        self._strong_parts: list[str] = []
        self._li_parts: list[str] = []
        self.category: str | None = None
        self.rows: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "strong":
            self._in_strong = True
            self._strong_parts = []
        elif lower == "li":
            self._in_li = True
            self._li_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "strong" and self._in_strong:
            self._in_strong = False
            text = _normalize_ws("".join(self._strong_parts))
            if text and _looks_like_category(text):
                self.category = text
        elif lower == "li" and self._in_li:
            self._in_li = False
            text = _normalize_ws("".join(self._li_parts))
            if text and self.category:
                self.rows.append((self.category, text))

    def handle_data(self, data: str) -> None:
        if self._in_strong:
            self._strong_parts.append(data)
        if self._in_li:
            self._li_parts.append(data)


def parse_locus_html(
    html: str, *, year: int, award: AwardSlug
) -> dict[str, Any]:
    """Parse a Locus list HTML page into a Living List payload.

    Works for Locus Awards top-ten finalist posts and Recommended Reading
    list posts (same unread-safe Title, Creator markup).

    Args:
        html: Raw HTML from a Locus list article.
        year: List year (award year or RRL coverage year).
        award: Payload award slug (``locus`` or ``locus-rrl``).

    Returns:
        Payload dict with ``award``, ``year``, and ``members``.
    """
    parser = _LocusListParser()
    parser.feed(html)
    members: list[dict[str, Any]] = []
    for category, line in parser.rows:
        item = _member_from_line(line, category=category, year=year)
        if item is not None:
            members.append(item)
    return {
        "award": award,
        "year": year,
        "members": members,
    }


def refresh_locus(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse Locus Awards HTML and write a Living List Finding.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the awards top-ten page.
        year: Award year.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``locus-{year}``).
    """
    return _refresh_locus_award(
        cache_dir=cache_dir,
        html=html,
        year=year,
        source_url=source_url,
        fetched_at=fetched_at,
        award="locus",
        finding_id=f"locus-{year}",
    )


def refresh_locus_rrl(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse Locus Recommended Reading HTML and write a Living List Finding.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the Recommended Reading list page.
        year: Coverage year of the Recommended Reading list.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``locus-rrl-{year}``).
    """
    return _refresh_locus_award(
        cache_dir=cache_dir,
        html=html,
        year=year,
        source_url=source_url,
        fetched_at=fetched_at,
        award="locus-rrl",
        finding_id=f"locus-rrl-{year}",
    )


def _refresh_locus_award(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None,
    award: AwardSlug,
    finding_id: str,
) -> str:
    payload = parse_locus_html(html, year=year, award=award)
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=finding_id,
        award=award,
        year=year,
        members=payload["members"],
        source_url=source_url,
        fetched_at=fetched_at,
    )


def fetch_locus_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch a Locus list page over HTTP.

    Args:
        url: Official Locus article URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8.
    """
    return fetch_html(url, timeout=timeout)


def _member_from_line(
    line: str, *, category: str, year: int
) -> dict[str, Any] | None:
    # Drop trailing purchase-link noise if any leaked into the line text.
    cleaned = re.split(r"\bamazon\b|\bbookshop\b", line, maxsplit=1)[0]
    cleaned = _normalize_ws(cleaned)
    match = _TITLE_CREATOR.match(cleaned)
    if match:
        title = match.group("title").strip()
        creator = match.group("creator").strip()
        if title and creator:
            return member(title, creator, category, year)
        return None
    # Person / magazine / publisher-only finalists (no "Title, Creator" form).
    name = cleaned.strip("\"“”'")
    if name:
        return member(name, name, category, year)
    return None


def _looks_like_category(text: str) -> bool:
    """Return True for Locus section headings, not work titles in <strong>."""
    if _PROSE_NOISE.search(text):
        return False
    if "," in text or ":" in text:
        return False
    if len(text) > 48:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio < 0.7:
        return False
    return bool(_CATEGORY_HINT.search(text))


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
