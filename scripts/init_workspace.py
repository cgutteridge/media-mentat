#!/usr/bin/env python3
"""Initialize a blank private workspace; never overwrite an existing profile."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recommender_workspace.setup import init_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        created = init_workspace(args.workspace)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    for path in created:
        print(f"Created {path}")
    if not created:
        print("Existing records preserved; no files replaced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
