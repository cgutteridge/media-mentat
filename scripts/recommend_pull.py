#!/usr/bin/env python3
"""Run recommend pull: Evidence gate over active Findings + members by medium.

Examples:
  python3 scripts/recommend_pull.py
  python3 scripts/recommend_pull.py --medium screen
  python3 scripts/recommend_pull.py --medium short
  python3 scripts/recommend_pull.py --cache-dir findings --grilling-record taste/grilling-record.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recommend_pull.pull import (  # noqa: E402
    MEDIUM_BOOKS,
    VALID_MEDIA,
    format_pull_report,
    recommend_pull,
)


from recommender_workspace.paths import private_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry: load Findings, evaluate Evidence gate, print pull report.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on success; 2 when gate is not ``allow``).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Load active Finding cache records, run the Evidence gate, "
            "and print Living List members for the requested medium."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.cwd() / "findings",
        help="Finding cache directory (default: ./findings)",
    )
    parser.add_argument(
        "--grilling-record",
        type=Path,
        default=Path.cwd() / "taste" / "grilling-record.md",
        help="Grilling record path (default: ./taste/grilling-record.md)",
    )
    parser.add_argument(
        "--medium",
        choices=sorted(VALID_MEDIA),
        default=MEDIUM_BOOKS,
        help=(
            "Member filter: books (novel/novella, default), "
            "screen (Dramatic Presentation), or short "
            "(short story / novelette / short fiction)."
        ),
    )
    parser.add_argument(
        "--require",
        action="append",
        default=None,
        metavar="FINDING_ID",
        help=(
            "Required finding id (repeatable). "
            "Default: every loaded active finding id."
        ),
    )
    args = parser.parse_args(argv)
    try:
        args.cache_dir = private_path(args.cache_dir)
    except ValueError as exc:
        parser.error(str(exc))

    result = recommend_pull(
        cache_dir=args.cache_dir,
        grilling_record=args.grilling_record,
        medium=args.medium,
        required_finding_ids=args.require,
    )
    sys.stdout.write(format_pull_report(result))
    return 0 if result.decision == "allow" else 2


if __name__ == "__main__":
    raise SystemExit(main())
