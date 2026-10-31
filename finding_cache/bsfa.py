"""BSFA Awards Living List parse and refresh."""

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

_BEST_CATEGORY = re.compile(r"^Best\b", re.IGNORECASE)
_PUBLISHED_YEAR = re.compile(
    r"work published in\s+(?P<year>20\d{2})",
    re.IGNORECASE,
)
_HEADER_CELLS = {"title", "author", "publisher", "link", "venue", "artist"}


class _BsfaListParser(HTMLParser):
    """Extract Best-* h1 categories and Title/Author table rows."""

    def __init__(self) -> None:
        super().__init__()
        self._in_h1 = False
        self._in_td = False
        self._in_tr = False
        self._h1_parts: list[str] = []
        self._td_parts: list[str] = []
        self._row_cells: list[str] = []
        self.category: str | None = None
        self.rows: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "h1":
            self._in_h1 = True
            self._h1_parts = []
        elif lower == "tr":
            self._in_tr = True
            self._row_cells = []
        elif lower == "td" and self._in_tr:
            self._in_td = True
            self._td_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "h1" and self._in_h1:
            self._in_h1 = False
            text = _normalize_ws("".join(self._h1_parts))
            if text and _BEST_CATEGORY.match(text):
                self.category = text
        elif lower == "td" and self._in_td:
            self._in_td = False
            self._row_cells.append(_normalize_ws("".join(self._td_parts)))
        elif lower == "tr" and self._in_tr:
            self._in_tr = False
            if self.category and len(self._row_cells) >= 2:
                title, creator = self._row_cells[0], self._row_cells[1]
                if title and creator and not _is_header_row(title, creator):
                    self.rows.append((self.category, title, creator))

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            self._h1_parts.append(data)
        if self._in_td:
            self._td_parts.append(data)


def detect_bsfa_year(html: str) -> int | None:
    """Return the ballot publication year mentioned on a BSFA shortlist page.

    Args:
        html: Raw HTML from the official BSFA shortlist page.

    Returns:
        Detected year, or ``None`` if the page does not state one.
    """
    match = _PUBLISHED_YEAR.search(html)
    return int(match.group("year")) if match else None


def parse_bsfa_html(html: str, *, year: int) -> dict[str, Any]:
    """Parse a BSFA shortlist HTML page into a Living List payload.

    Extracts unread-safe title/creator/category/year signals from category
    tables (Title / Author columns).

    Args:
        html: Raw HTML from the official BSFA shortlist page.
        year: Award year for the Living List (publication year for the ballot).

    Returns:
        Payload dict with ``award``, ``year``, and ``members``.

    Raises:
        ValueError: If the page states a different publication year than
            ``year``.
    """
    detected = detect_bsfa_year(html)
    if detected is not None and detected != year:
        raise ValueError(
            f"BSFA page is for work published in {detected}, "
            f"but refresh year was {year}"
        )
    parser = _BsfaListParser()
    parser.feed(html)
    members = [
        member(title, creator, category, year)
        for category, title, creator in parser.rows
    ]
    return {
        "award": "bsfa",
        "year": year,
        "members": members,
    }


def refresh_bsfa(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse BSFA HTML and write/update a Living List Finding in the cache.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the shortlist page.
        year: Award / ballot year.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``bsfa-{year}``).
    """
    payload = parse_bsfa_html(html, year=year)
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=f"bsfa-{year}",
        award="bsfa",
        year=year,
        members=payload["members"],
        source_url=source_url,
        fetched_at=fetched_at,
    )


def bsfa_shortlist_url() -> str:
    """Return the canonical BSFA awards shortlist URL.

    Returns:
        Official bsfa.co.uk shortlist page URL.
    """
    return "https://www.bsfa.co.uk/bsfa-awards-shortlist/"


def fetch_bsfa_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch BSFA shortlist page HTML over HTTP.

    Args:
        url: Official BSFA shortlist page URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8.
    """
    return fetch_html(url, timeout=timeout)


def _is_header_row(title: str, creator: str) -> bool:
    return title.casefold() in _HEADER_CELLS or creator.casefold() in _HEADER_CELLS


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
