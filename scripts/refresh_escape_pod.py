#!/usr/bin/env python3
"""Refresh Escape Pod RSS into the Finding cache.

Examples:
  python3 scripts/refresh_escape_pod.py
  python3 scripts/refresh_escape_pod.py --rss-file finding_cache/fixtures/escape_pod_feed_snippet.xml
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finding_cache.rss_feeds import (  # noqa: E402
    ESCAPE_POD_FEED_URL,
    fetch_rss,
    refresh_escape_pod,
)
from finding_cache.store import load_finding  # noqa: E402


from recommender_workspace.paths import private_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry: fetch or read Escape Pod RSS, write Finding cache.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Refresh Escape Pod RSS Living List into findings/",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.cwd() / "findings",
        help="Finding cache directory (default: ./findings)",
    )
    parser.add_argument(
        "--url",
        default=ESCAPE_POD_FEED_URL,
        help="Feed URL (default: Escape Pod podcast feed)",
    )
    parser.add_argument(
        "--rss-file",
        type=Path,
        default=None,
        help="Read RSS from a local file instead of fetching",
    )
    args = parser.parse_args(argv)
    try:
        args.cache_dir = private_path(args.cache_dir)
    except ValueError as exc:
        parser.error(str(exc))

    if args.rss_file is not None:
        rss_text = args.rss_file.read_text(encoding="utf-8")
    else:
        rss_text = fetch_rss(args.url)

    finding_id = refresh_escape_pod(
        cache_dir=args.cache_dir,
        rss_text=rss_text,
        source_url=args.url,
        fetched_at=datetime.now(timezone.utc),
    )
    record = load_finding(args.cache_dir, finding_id)
    members = record["payload"].get("members", [])
    print(
        f"Wrote {finding_id} ({len(members)} members) → "
        f"{args.cache_dir / f'{finding_id}.json'}"
    )
    print(f"Source: {args.url}")
    print(f"Fetched at: {record['fetched_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
