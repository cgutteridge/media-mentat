"""Hugo Awards Living List parse and refresh."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from evidence_gate.gate import (
    LIVING_LIST_MAX_AGE_SECONDS,
    LIVING_LIST_SOFT_REUSE_SECONDS,
)
from finding_cache.store import write_finding

_BY_SPLIT = re.compile(
    r"(?<!translated)\s+by\s+",
    re.IGNORECASE,
)
_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")
_TRANSLATED_BY_TAIL = re.compile(
    r",?\s*translated by\s+.+$",
    re.IGNORECASE,
)
_QUOTED_TITLE_CREATOR = re.compile(
    r'^[\"“”\'](?P<title>.+?)[\"“”\']\s*,\s*(?P<creator>.+)$'
)
_BALLOT_NOISE = re.compile(
    r"^\d+\s+ballots?\b",
    re.IGNORECASE,
)


class _HugoListParser(HTMLParser):
    """Extract category headings and list-item nominee lines.

    Official Hugo history pages mark categories as
    ``<p><strong>Best Novel</strong></p>`` (not ``<h3>``). Older/fixture
    markup may still use ``h3``; both are accepted.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_heading = False
        self._in_strong = False
        self._in_li = False
        self._heading_parts: list[str] = []
        self._strong_parts: list[str] = []
        self._li_parts: list[str] = []
        self.category: str | None = None
        self.rows: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in {"h2", "h3", "h4"}:
            self._in_heading = True
            self._heading_parts = []
        elif lower == "strong":
            self._in_strong = True
            self._strong_parts = []
        elif lower == "li":
            self._in_li = True
            self._li_parts = []

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"h2", "h3", "h4"} and self._in_heading:
            self._in_heading = False
            text = _normalize_ws("".join(self._heading_parts))
            if text and _looks_like_hugo_category(text):
                self.category = text
        elif lower == "strong" and self._in_strong:
            self._in_strong = False
            text = _normalize_ws("".join(self._strong_parts))
            if text and _looks_like_hugo_category(text):
                self.category = text
        elif lower == "li" and self._in_li:
            self._in_li = False
            text = _normalize_ws("".join(self._li_parts))
            if text and self.category and not _BALLOT_NOISE.match(text):
                self.rows.append((self.category, text))

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_parts.append(data)
        if self._in_strong:
            self._strong_parts.append(data)
        if self._in_li:
            self._li_parts.append(data)


def parse_hugo_html(html: str, *, year: int) -> dict[str, Any]:
    """Parse a Hugo history/finalists HTML page into a Living List payload.

    Extracts unread-safe title/creator/category/year signals only.

    Args:
        html: Raw HTML from an official Hugo awards year page.
        year: Award year for the Living List (e.g. 2024).

    Returns:
        Payload dict with ``award``, ``year``, and ``members``.
    """
    parser = _HugoListParser()
    parser.feed(html)
    members: list[dict[str, Any]] = []
    for category, line in parser.rows:
        member = _member_from_line(line, category=category, year=year)
        if member is not None:
            members.append(member)
    return {
        "award": "hugo",
        "year": year,
        "members": members,
    }


def refresh_hugo(
    *,
    cache_dir: Path,
    html: str,
    year: int,
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Parse Hugo HTML and write/update a Living List Finding in the cache.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        html: Raw HTML for the award year page.
        year: Award year.
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written (``hugo-{year}``).
    """
    stamp = fetched_at if fetched_at is not None else datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    payload = parse_hugo_html(html, year=year)
    finding_id = f"hugo-{year}"
    record = {
        "finding_id": finding_id,
        "kind": "living_list",
        "payload": payload,
        "source_refs": [source_url],
        "fetched_at": stamp.isoformat(),
        "max_age_seconds": LIVING_LIST_MAX_AGE_SECONDS,
        "swr_seconds": LIVING_LIST_SOFT_REUSE_SECONDS,
        "status": "active",
    }
    write_finding(cache_dir, record)
    return finding_id


def fetch_hugo_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch Hugo awards page HTML over HTTP.

    Args:
        url: Official Hugo history or finalists page URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8 (with replacement for bad bytes).
    """
    request = Request(
        url,
        headers={"User-Agent": "fiction-recommender-finding-cache/0.1"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def hugo_history_url(year: int) -> str:
    """Return the canonical Hugo history URL for ``year``.

    Args:
        year: Award year.

    Returns:
        Official thehugoawards.org history page URL.
    """
    return f"https://www.thehugoawards.org/hugo-history/{year}-hugo-awards/"


def _member_from_line(
    line: str, *, category: str, year: int
) -> dict[str, Any] | None:
    cleaned = _TRAILING_PAREN.sub("", line).strip()
    cleaned = _TRANSLATED_BY_TAIL.sub("", cleaned).strip()
    if not cleaned:
        return None

    quoted = _QUOTED_TITLE_CREATOR.match(cleaned)
    if quoted:
        title = quoted.group("title").strip()
        creator = _primary_creator(quoted.group("creator"))
        if title and creator:
            return _member(title, creator, category, year)

    parts = _BY_SPLIT.split(cleaned, maxsplit=1)
    if len(parts) == 2:
        title = parts[0].strip().strip("\"“”'")
        creator = _primary_creator(parts[1])
        if title and creator:
            return _member(title, creator, category, year)

    # Person-only / single-name finalists
    name = cleaned.strip("\"“”'")
    return _member(name, name, category, year)


def _primary_creator(raw: str) -> str:
    """Take the first author signal before bilingual / credit commas."""
    text = raw.strip()
    # Prefer Latin name before a bilingual slash form: "He Xi / 人生不相见, 何夕"
    if " / " in text:
        text = text.split(" / ", maxsplit=1)[0].strip()
    return text.split(",")[0].strip()


def _member(
    title: str, creator: str, category: str, year: int
) -> dict[str, Any]:
    return {
        "title": title,
        "creator": creator,
        "category": category,
        "year": year,
    }


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


_CATEGORY_PREFIXES = (
    "Best ",
    "Lodestar ",
    "Astounding ",
)


def _looks_like_hugo_category(text: str) -> bool:
    """Return True if strong-text looks like a Hugo category heading."""
    return text.startswith(_CATEGORY_PREFIXES)
