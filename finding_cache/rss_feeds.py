"""Parse magazine/podcast RSS into Unread-safe Living List members."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from finding_cache.living_list import USER_AGENT, member, write_living_list_finding

_TITLE_BY = re.compile(
    r"^(?P<title>.+?)\s+by\s+(?P<creator>.+)$",
    re.IGNORECASE,
)

# RSS / Atom / Dublin Core namespaces commonly seen on magazine feeds.
_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "atom": "http://www.w3.org/2005/Atom",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
}

CLARKESWORLD_FEED_URL = "https://clarkesworldmagazine.com/feed/"
ESCAPE_POD_FEED_URL = "https://feeds.escapepod.org/EscapePod"


def fetch_rss(url: str, *, timeout: float = 30.0) -> str:
    """Fetch an RSS/Atom document over HTTP.

    Args:
        url: Feed URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8 (replacement for bad bytes).
    """
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def parse_short_fiction_rss(
    xml_text: str,
    *,
    category: str = "Short Fiction",
) -> list[dict[str, Any]]:
    """Parse RSS items into Unread-safe Living List members.

    Extracts title, creator, category, year (from pubDate). Ignores plot
    description / content bodies for pitch text. Skips items that look like
    non-fiction (interviews, editorials) when category tags say so.

    Args:
        xml_text: Raw RSS/XML document.
        category: Default member category when feed categories are noisy.

    Returns:
        List of member dicts (title, creator, category, year).
    """
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall(
        "atom:entry", _NS
    )
    if not items and channel is None:
        items = root.findall("item")

    members: list[dict[str, Any]] = []
    for item in items:
        if _looks_non_fiction_item(item):
            continue
        title_el = item.find("title")
        raw_title = _text(title_el)
        if not raw_title:
            continue
        title, creator_from_title = _split_title_by(raw_title)
        creator = (
            _text(item.find("dc:creator", _NS))
            or _text(item.find("author"))
            or _text(item.find("itunes:author", _NS))
            or creator_from_title
            or "Unknown"
        )
        if creator_from_title and creator == "Unknown":
            creator = creator_from_title
        # Prefer explicit dc:creator over "by" split when both exist.
        if _text(item.find("dc:creator", _NS)):
            title = raw_title
            # Strip trailing " by Author" when creator is already known.
            split_title, split_creator = _split_title_by(raw_title)
            if split_creator and split_creator.lower() == creator.lower():
                title = split_title
        year = _year_from_item(item)
        members.append(member(title, creator, category, year))
    return members


def refresh_clarkesworld(
    *,
    cache_dir: Path,
    rss_text: str,
    source_url: str = CLARKESWORLD_FEED_URL,
    fetched_at: datetime | None = None,
    finding_id: str = "clarkesworld-rss",
) -> str:
    """Write a Clarkesworld RSS Living List Finding and return its id.

    Args:
        cache_dir: Finding cache directory.
        rss_text: Raw RSS XML.
        source_url: Canonical feed URL for ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).
        finding_id: Cache id to write.

    Returns:
        The ``finding_id`` written.
    """
    members = parse_short_fiction_rss(
        rss_text, category="Clarkesworld Short Fiction"
    )
    year = _dominant_year(members) or datetime.now(timezone.utc).year
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=finding_id,
        award="clarkesworld",
        year=year,
        members=members,
        source_url=source_url,
        fetched_at=fetched_at,
    )


def refresh_escape_pod(
    *,
    cache_dir: Path,
    rss_text: str,
    source_url: str = ESCAPE_POD_FEED_URL,
    fetched_at: datetime | None = None,
    finding_id: str = "escape-pod-rss",
) -> str:
    """Write an Escape Pod RSS Living List Finding and return its id.

    Args:
        cache_dir: Finding cache directory.
        rss_text: Raw RSS XML.
        source_url: Canonical feed URL for ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).
        finding_id: Cache id to write.

    Returns:
        The ``finding_id`` written.
    """
    members = parse_short_fiction_rss(
        rss_text, category="Escape Pod Short Fiction"
    )
    year = _dominant_year(members) or datetime.now(timezone.utc).year
    return write_living_list_finding(
        cache_dir=cache_dir,
        finding_id=finding_id,
        award="escape-pod",
        year=year,
        members=members,
        source_url=source_url,
        fetched_at=fetched_at,
    )


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return " ".join(el.text.split()).strip()


def _split_title_by(raw: str) -> tuple[str, str]:
    match = _TITLE_BY.match(raw.strip())
    if not match:
        return raw.strip(), ""
    return match.group("title").strip(), match.group("creator").strip()


def _year_from_item(item: ET.Element) -> int:
    for tag in ("pubDate", "published", "updated"):
        el = item.find(tag)
        if el is None:
            el = item.find(f"atom:{tag}", _NS)
        text = _text(el)
        if not text:
            continue
        try:
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError, IndexError):
            try:
                dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.year
    return datetime.now(timezone.utc).year


def _looks_non_fiction_item(item: ET.Element) -> bool:
    cats = [
        _text(c).lower()
        for c in item.findall("category")
        if _text(c)
    ]
    joined = " ".join(cats)
    for noise in ("interview", "editorial", "non-fiction", "nonfiction", "podcast:trailer"):
        if noise in joined:
            return True
    title = _text(item.find("title")).lower()
    return title.startswith("interview:") or " editor's desk" in title


def _dominant_year(members: list[dict[str, Any]]) -> int | None:
    if not members:
        return None
    years = [int(m["year"]) for m in members if m.get("year") is not None]
    if not years:
        return None
    return max(set(years), key=years.count)
