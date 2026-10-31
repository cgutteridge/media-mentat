"""Arthur C. Clarke Award Living List parse and refresh."""

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

_YEAR_ONLY = re.compile(r"^(19|20)\d{2}$")
# Require whitespace around the separator so hyphenated titles
# (e.g. Chain-Gang All-Stars) are not split.
_TITLE_CREATOR = re.compile(
    r"^(?P<title>.+?)\s+[-–—]\s+(?P<creator>.+?)(?:\s+[-–—]\s+WINNER)?$",
    re.IGNORECASE,
)
_WINNER_TAIL = re.compile(r"\s+[-–—]\s+WINNER\s*$", re.IGNORECASE)


class _ClarkeHomeParser(HTMLParser):
    """Extract year-scoped shortlist lines from clarkeaward.com markup."""

    def __init__(self) -> None:
        super().__init__()
        self._in_em = False
        self._in_block = False
        self._em_parts: list[str] = []
        self._block_parts: list[str] = []
        self.current_year: int | None = None
        # (year, line)
        self.rows: list[tuple[int, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        attrs_dict = {k: (v or "") for k, v in attrs}
        if lower == "em":
            self._in_em = True
            self._em_parts = []
        elif lower == "span" and "p" in attrs_dict.get("class", "").split():
            self._in_block = True
            self._block_parts = []
        elif lower == "br" and self._in_block:
            self._flush_block_fragment()

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "em" and self._in_em:
            self._in_em = False
            text = _normalize_ws("".join(self._em_parts))
            if _YEAR_ONLY.match(text):
                self.current_year = int(text)
        elif lower == "span" and self._in_block:
            self._in_block = False
            self._flush_block_fragment()

    def handle_data(self, data: str) -> None:
        if self._in_em:
            self._em_parts.append(data)
        if self._in_block:
            self._block_parts.append(data)

    def _flush_block_fragment(self) -> None:
        text = _normalize_ws("".join(self._block_parts))
        self._block_parts = []
        if not text or self.current_year is None:
            return
        if _YEAR_ONLY.match(text):
            return
        self.rows.append((self.current_year, text))


def parse_clarke_html(html: str, *, year: int) -> dict[str, Any]:
    """Parse Clarke Award HTML into a Living List payload for ``year``.

    Supports clarkeaward.com year blocks (``Title - Creator`` lines).

    Args:
        html: Raw HTML from the award site (or equivalent fixture).
        year: Award year for the Living List (e.g. 2024).

    Returns:
        Payload dict with ``award``, ``year``, and ``members``.
    """
    parser = _ClarkeHomeParser()
    parser.feed(html)
    members: list[dict[str, Any]] = []
    for row_year, line in parser.rows:
        if row_year != year:
            continue
        item = _member_from_line(line, year=year)
        if item is not None:
            members.append(item)
    return {
        "award": "clarke",
        "year": year,
        "members": members,
    }


def refresh_clarke(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse Clarke HTML and write/update a Living List Finding in the cache.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the award page.
        year: Award year.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``clarke-{year}``).
    """
    payload = parse_clarke_html(html, year=year)
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=f"clarke-{year}",
        award="clarke",
        year=year,
        members=payload["members"],
        source_url=source_url,
        fetched_at=fetched_at,
    )


def clarke_home_url() -> str:
    """Return the canonical Clarke Award homepage URL.

    Returns:
        Official clarkeaward.com URL (multi-year shortlist archive).
    """
    return "https://www.clarkeaward.com/"


def fetch_clarke_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch Clarke Award page HTML over HTTP.

    Args:
        url: Official Clarke page URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8.
    """
    return fetch_html(url, timeout=timeout)


def _member_from_line(line: str, *, year: int) -> dict[str, Any] | None:
    cleaned = _WINNER_TAIL.sub("", line).strip()
    cleaned = _normalize_ws(cleaned.replace("\xa0", " "))
    match = _TITLE_CREATOR.match(cleaned)
    if not match:
        return None
    title = match.group("title").strip()
    creator = match.group("creator").strip()
    if not title or not creator:
        return None
    return member(title, creator, "Novel", year)


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
