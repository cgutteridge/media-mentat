#!/usr/bin/env python3
"""Check the exact public-file boundary; content still needs human review."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv"}
# Generic identifiers only. Never embed the private user's actual details here.
PRIVATE_CONTENT = re.compile(
    r"/" r"Users/[^/\s]+/|/" r"home/[^/\s]+/|[A-Z]:\\Users\\[^\\\s]+\\"
    r"|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"
    r"|https://docs\.google\.com/document/d/[A-Za-z0-9_-]+"
)


def read_allowlist(root: Path) -> set[str]:
    paths = set((root / "PUBLIC_FILES.txt").read_text(encoding="utf-8").splitlines())
    for name in paths:
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or str(path) != name:
            raise ValueError("invalid public allowlist entry")
    return paths


def check_tree(root: Path) -> list[str]:
    """Reject extra files, links, missing approved files and obvious private data."""
    allowed = read_allowlist(root)
    problems = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        for name in list(subdirs):
            path = Path(directory) / name
            if path.is_symlink():
                problems.append(f"symlink directory: {path.relative_to(root)}")
                subdirs.remove(name)
            elif name in RUNTIME_DIRS:
                subdirs.remove(name)
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                problems.append(f"symlink file: {relative}")
            elif relative not in allowed:
                problems.append(f"file outside publication allowlist: {relative}")
            else:
                try:
                    content = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    problems.append(f"unreadable/non-text public file: {relative}")
                    continue
                if PRIVATE_CONTENT.search(content):
                    # Never echo matching private content to the output.
                    problems.append(f"possible private content: {relative}")
    for name in sorted(allowed):
        if not (root / name).is_file():
            problems.append(f"missing approved file: {name}")
    return problems


def check_git(root: Path) -> list[str]:
    """Inspect this repository only, never an enclosing private repository."""
    if not (root / ".git").exists():
        return ["public package needs its own Git repository"]
    allowed = read_allowlist(root)

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)

    tracked = git("ls-files", "--stage", "-z")
    if tracked.returncode:
        return ["cannot inspect public Git index"]
    problems = []
    checked_blobs = set()

    def check_entries(raw: bytes, surface: str) -> None:
        for entry in raw.decode().split("\0"):
            if not entry:
                continue
            metadata, name = entry.split("\t", 1)
            mode, middle, last = metadata.split()
            object_id = middle if surface == "tracked" else last
            if name not in allowed:
                problems.append(f"{surface} file outside publication allowlist: {name}")
            if mode not in {"100644", "100755"}:
                problems.append(f"{surface} non-regular file: {name}")
                continue
            if object_id in checked_blobs:
                continue
            checked_blobs.add(object_id)
            blob = git("cat-file", "blob", object_id)
            if blob.returncode:
                problems.append(f"cannot inspect {surface} content: {name}")
                continue
            try:
                content = blob.stdout.decode("utf-8")
            except UnicodeError:
                problems.append(f"{surface} non-text content: {name}")
                continue
            if PRIVATE_CONTENT.search(content):
                problems.append(f"possible private content in {surface}: {name}")

    check_entries(tracked.stdout, "tracked")
    # Git history is a separate publication surface. Path checks are a backstop;
    # current allowlist entries still need content review throughout history.
    commits = git("rev-list", "--all")
    if commits.returncode:
        return problems + ["cannot inspect public Git history"]
    for commit in commits.stdout.decode().splitlines():
        tree = git("ls-tree", "-r", "-z", commit)
        if tree.returncode:
            problems.append("cannot inspect a committed public tree")
            continue
        check_entries(tree.stdout, "committed")
    return problems


def main() -> int:
    try:
        problems = check_tree(ROOT) + check_git(ROOT)
    except (OSError, ValueError) as exc:
        print(f"Public boundary check failed: {exc}", file=sys.stderr)
        return 1
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print("Public file boundary checks passed. Review content before publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
