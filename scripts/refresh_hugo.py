#!/usr/bin/env python3
"""Manually refresh the Hugo Living List into the Finding cache.

Examples:
  python scripts/refresh_hugo.py --year 2024
  python scripts/refresh_hugo.py --year 2024 --html-file path/to/page.html
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finding_cache.hugo import (  # noqa: E402
    fetch_hugo_html,
    hugo_history_url,
    refresh_hugo,
)
from finding_cache.store import load_finding  # noqa: E402


from recommender_workspace.paths import private_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry: fetch or read Hugo HTML, write Finding cache, print summary.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Refresh Hugo Awards Living List into findings/",
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Hugo award year (e.g. 2024)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.cwd() / "findings",
        help="Finding cache directory (default: ./findings)",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Override source URL (default: official Hugo history page)",
    )
    parser.add_argument(
        "--html-file",
        type=Path,
        default=None,
        help="Read HTML from a local file instead of fetching",
    )
    args = parser.parse_args(argv)
    try:
        args.cache_dir = private_path(args.cache_dir)
    except ValueError as exc:
        parser.error(str(exc))

    source_url = args.url or hugo_history_url(args.year)
    if args.html_file is not None:
        html = args.html_file.read_text(encoding="utf-8")
    else:
        html = fetch_hugo_html(source_url)

    fetched_at = datetime.now(timezone.utc)
    finding_id = refresh_hugo(
        cache_dir=args.cache_dir,
        html=html,
        year=args.year,
        source_url=source_url,
        fetched_at=fetched_at,
    )
    record = load_finding(args.cache_dir, finding_id)
    members = record["payload"].get("members", [])
    print(
        f"Wrote {finding_id} ({len(members)} members) → "
        f"{args.cache_dir / f'{finding_id}.json'}"
    )
    print(f"Source: {source_url}")
    print(f"Fetched at: {record['fetched_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
