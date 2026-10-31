"""Finding cache store: JSON files under a findings directory."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from evidence_gate.gate import Finding, FindingKind
from recommender_workspace.paths import private_path

_REQUIRED_FIELDS = (
    "finding_id",
    "kind",
    "payload",
    "source_refs",
    "fetched_at",
    "max_age_seconds",
    "status",
)

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def write_finding(cache_dir: Path, record: Mapping[str, Any]) -> Path:
    """Write a Finding record to ``cache_dir``, soft-staling any prior active file.

    Args:
        cache_dir: Directory that holds Finding JSON files.
        record: Finding dict with at least finding_id, kind, payload,
            source_refs, fetched_at, and status.

    Returns:
        Path to the written active finding file.

    Raises:
        ValueError: If required fields are missing or finding_id is unsafe.
    """
    _validate_record(record)
    finding_id = str(record["finding_id"])
    cache_dir = private_path(cache_dir)
    # Validate final paths too: a pre-existing cache file may itself be a link.
    private_path(cache_dir / f"{finding_id}.json")
    cache_dir.mkdir(parents=True, exist_ok=True)
    active_path = cache_dir / f"{finding_id}.json"

    if active_path.exists():
        previous = json.loads(active_path.read_text(encoding="utf-8"))
        archived = dict(previous)
        archived["status"] = "soft-stale"
        stamp = _archive_stamp(previous.get("fetched_at", ""))
        archive_path = cache_dir / f"{finding_id}.{stamp}.json"
        private_path(archive_path)
        archive_path.write_text(
            json.dumps(archived, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    active_path.write_text(
        json.dumps(dict(record), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return active_path


def load_finding(cache_dir: Path, finding_id: str) -> dict[str, Any]:
    """Load a Finding JSON record by id or archive stem.

    Args:
        cache_dir: Directory that holds Finding JSON files.
        finding_id: Active finding id (``hugo-2024``) or archive stem
            (``hugo-2024.2026-01-01T00-00-00+00-00``).

    Returns:
        The Finding record as a dict.

    Raises:
        FileNotFoundError: If no matching file exists.
        ValueError: If finding_id is unsafe.
    """
    if not _SAFE_ID.match(finding_id):
        raise ValueError(f"unsafe finding_id: {finding_id!r}")
    path = cache_dir / f"{finding_id}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"finding file is not an object: {path}")
    return data


def to_gate_finding(record: Mapping[str, Any]) -> Finding:
    """Convert a cache record into an Evidence gate :class:`Finding`.

    Args:
        record: Finding dict from the cache store.

    Returns:
        A gate Finding with freshness fields mapped for evaluation.
    """
    kind = FindingKind(str(record["kind"]))
    fetched_at = _parse_datetime(record["fetched_at"])
    validated_raw = record.get("validated_at")
    validated_at = (
        _parse_datetime(validated_raw) if validated_raw is not None else None
    )
    return Finding(
        finding_id=str(record["finding_id"]),
        kind=kind,
        fetched_at=fetched_at,
        validated_at=validated_at,
        max_age_seconds=record.get("max_age_seconds"),
        swr_seconds=record.get("swr_seconds"),
        status=str(record.get("status", "active")),
    )


def _validate_record(record: Mapping[str, Any]) -> None:
    missing = [field for field in _REQUIRED_FIELDS if field not in record]
    if missing:
        raise ValueError(f"finding record missing fields: {missing}")
    finding_id = str(record["finding_id"])
    if not _SAFE_ID.match(finding_id):
        raise ValueError(f"unsafe finding_id: {finding_id!r}")


def _archive_stamp(fetched_at: str) -> str:
    """Build a filesystem-safe stamp from an ISO fetched_at value."""
    cleaned = (
        fetched_at.replace(":", "-").replace("+", "p").replace("/", "-")
    )
    return cleaned if cleaned else "unknown"


def _parse_datetime(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)
