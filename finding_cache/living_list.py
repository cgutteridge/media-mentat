"""Shared helpers for Living List refresh into the Finding cache."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen

from evidence_gate.gate import (
    LIVING_LIST_MAX_AGE_SECONDS,
    LIVING_LIST_SOFT_REUSE_SECONDS,
)
from finding_cache.store import write_finding

USER_AGENT = "fiction-recommender-finding-cache/0.1"


def fetch_html(url: str, *, timeout: float = 30.0) -> str:
    """Fetch an award list page over HTTP.

    Args:
        url: Official list page URL.
        timeout: Socket timeout in seconds.

    Returns:
        Response body decoded as UTF-8 (with replacement for bad bytes).
    """
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def write_living_list_finding(
    *,
    cache_dir: Path,
    finding_id: str,
    award: str,
    year: int,
    members: Sequence[Mapping[str, Any]],
    source_url: str,
    fetched_at: datetime | None = None,
) -> str:
    """Write a Living List Finding record and return its id.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).
        finding_id: Cache id (e.g. ``nebula-2024``).
        award: Award slug stored in payload (e.g. ``nebula``).
        year: List / award year.
        members: Unread-safe member dicts (title, creator, category, year).
        source_url: Canonical source URL stored in ``source_refs``.
        fetched_at: Fetch timestamp (UTC now if omitted).

    Returns:
        The ``finding_id`` written.
    """
    stamp = fetched_at if fetched_at is not None else datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    record = {
        "finding_id": finding_id,
        "kind": "living_list",
        "payload": {
            "award": award,
            "year": year,
            "members": list(members),
        },
        "source_refs": [source_url],
        "fetched_at": stamp.isoformat(),
        "max_age_seconds": LIVING_LIST_MAX_AGE_SECONDS,
        "swr_seconds": LIVING_LIST_SOFT_REUSE_SECONDS,
        "status": "active",
    }
    write_finding(cache_dir, record)
    return finding_id


def member(
    title: str, creator: str, category: str, year: int
) -> dict[str, Any]:
    """Build an unread-safe Living List member dict.

    Args:
        title: Work title (or person name for person-only awards).
        creator: Primary creator signal.
        category: Award category / list section.
        year: Award or list year.

    Returns:
        Member mapping with title, creator, category, and year.
    """
    return {
        "title": title,
        "creator": creator,
        "category": category,
        "year": year,
    }
