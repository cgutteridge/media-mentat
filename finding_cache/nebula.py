"""Nebula Awards Living List parse and refresh."""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from finding_cache.living_list import (
    fetch_html,
    member,
    write_living_list_finding,
)

_BY_SPLIT = re.compile(r"\s+by\s+", re.IGNORECASE)
_WINNER_PREFIX = re.compile(r"^Winner:\s*", re.IGNORECASE)
_CURLY_QUOTES = re.compile(r'^[\"“”\']|[\"“”\']$')


class _NebulaListParser(HTMLParser):
    """Extract h4 category headings and list-item nominee lines."""

    def __init__(self) -> None:
        super().__init__()
        self._in_h4 = False
        self._in_li = False
        self._h4_parts: list[str] = []
        self._li_parts: list[str] = []
        self.category: str | None = None
        self.rows: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "h4":
            self._in_h4 = True
            self._h4_parts = []
        elif lower == "li":
            self._in_li = True
            self._li_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "h4" and self._in_h4:
            self._in_h4 = False
            text = _normalize_ws("".join(self._h4_parts))
            if text:
                self.category = text
        elif lower == "li" and self._in_li:
            self._in_li = False
            text = _normalize_ws("".join(self._li_parts))
            if text and self.category:
                self.rows.append((self.category, text))

    def handle_data(self, data: str) -> None:
        if self._in_h4:
            self._h4_parts.append(data)
        if self._in_li:
            self._li_parts.append(data)


def parse_nebula_html(html: str, *, year: int) -> dict[str, Any]:
    """Parse a Nebula award-year HTML page into a Living List payload.

    Extracts unread-safe title/creator/category/year signals only.

    Args:
        html: Raw HTML from an official Nebula award-year page.
        year: Award year for the Living List (e.g. 2024).

    Returns:
        Payload dict with ``award``, ``year``, and ``members``.
    """
    parser = _NebulaListParser()
    parser.feed(html)
    members: list[dict[str, Any]] = []
    for category, line in parser.rows:
        item = _member_from_line(line, category=category, year=year)
        if item is not None:
            members.append(item)
    return {
        "award": "nebula",
        "year": year,
        "members": members,
    }


def refresh_nebula(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse Nebula HTML and write/update a Living List Finding in the cache.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the award year page.
        year: Award year.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``nebula-{year}``).
    """
    payload = parse_nebula_html(html, year=year)
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=f"nebula-{year}",
        award="nebula",
        year=year,
        members=payload["members"],
        source_url=source_url,
        fetched_at=fetched_at,
    )


def nebula_award_year_url(year: int) -> str:
    """Return the canonical Nebula award-year URL.

    Args:
        year: Award year.

    Returns:
        Official nebulas.sfwa.org award-year page URL.
    """
    return f"https://nebulas.sfwa.org/award-year/{year}/"


def fetch_nebula_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch Nebula awards page HTML over HTTP.

    Args:
        url: Official Nebula award-year page URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8.
    """
    return fetch_html(url, timeout=timeout)


def _member_from_line(
    line: str, *, category: str, year: int
) -> dict[str, Any] | None:
    cleaned = _WINNER_PREFIX.sub("", line).strip()
    # Drop publisher tail: ", published by ..."
    published_at = re.search(r",\s*published by\b", cleaned, re.IGNORECASE)
    if published_at:
        cleaned = cleaned[: published_at.start()].strip()
    if not cleaned:
        return None

    parts = _BY_SPLIT.split(cleaned, maxsplit=1)
    if len(parts) != 2:
        return None
    title = _strip_quotes(parts[0].strip())
    creator = parts[1].strip().split(",")[0].strip()
    if not title or not creator:
        return None
    return member(title, creator, category, year)


def _strip_quotes(text: str) -> str:
    return _CURLY_QUOTES.sub("", text).strip().strip("\"“”'")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
