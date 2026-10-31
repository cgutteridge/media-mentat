"""Load active Findings, evaluate the Evidence gate, and list members by medium."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from consumption_certainty.record import load_certainty_map
from evidence_gate.gate import GateResult, evaluate
from finding_cache.store import to_gate_finding

MEDIUM_BOOKS = "books"
MEDIUM_SCREEN = "screen"
MEDIUM_SHORT = "short"
VALID_MEDIA = frozenset({MEDIUM_BOOKS, MEDIUM_SCREEN, MEDIUM_SHORT})

# Categories matching novel/novella (case-insensitive substring), excluding novelette.
BOOKISH_CATEGORY_HINT = "novel/novella (excludes novelette)"
SCREEN_CATEGORY_HINT = "dramatic presentation"
SHORT_CATEGORY_HINT = "short story / novelette / short fiction"

SCREEN_LABEL_FILM = "film"
SCREEN_LABEL_TV_EPISODE = "tv-episode"


@dataclass(frozen=True)
class RecommendPullResult:
    """Outcome of a recommend pull: gate decision plus Living List members.

    Attributes:
        decision: Evidence gate decision value (``allow``, ``must-refresh``,
            ``clarify-or-refuse``).
        refresh_suggested: True when allow but soft-reuse advises a Research pass.
        missing_required_finding_ids: Required finding ids absent from the cache.
        blocked_finding_ids: Findings past soft-reuse that must not be pitched from.
        finding_ids: Active finding ids that were loaded and evaluated.
        medium: Pull medium (``books``, ``screen``, or ``short``).
        members: Living List members for that medium (Unread-safe fields only).
        spoiler_allowed: Per Stable Work id spoiler permission from the gate.
    """

    decision: str
    refresh_suggested: bool
    missing_required_finding_ids: tuple[str, ...]
    blocked_finding_ids: tuple[str, ...]
    finding_ids: tuple[str, ...]
    medium: str
    members: tuple[dict[str, Any], ...]
    spoiler_allowed: Mapping[str, bool]

    @property
    def book_members(self) -> tuple[dict[str, Any], ...]:
        """Backward-compatible alias for :attr:`members` when medium is books.

        Returns:
            Members when ``medium`` is ``books``; otherwise an empty tuple.
        """
        if self.medium == MEDIUM_BOOKS:
            return self.members
        return ()


def is_novel_or_novella_category(category: str) -> bool:
    """Return True when ``category`` is novel or novella (not novelette).

    Args:
        category: Award / list section label from a Living List member.

    Returns:
        True for novel/novella categories; False for novelette and other forms.
    """
    lowered = category.lower()
    if "novelette" in lowered:
        return False
    return "novella" in lowered or "novel" in lowered


def is_screen_category(category: str) -> bool:
    """Return True when ``category`` is a Dramatic Presentation award lane.

    Args:
        category: Award / list section label from a Living List member.

    Returns:
        True for Dramatic Presentation (long or short form) categories.
    """
    return "dramatic presentation" in category.lower()


def screen_form_label(category: str) -> str:
    """Map a Dramatic Presentation category to a report medium label.

    Hugo Long Form is labelled ``film``; Short Form is labelled ``tv-episode``.
    Other dramatic-presentation categories fall back to ``screen``.

    Args:
        category: Award / list section label from a Living List member.

    Returns:
        ``film``, ``tv-episode``, or ``screen``.
    """
    lowered = category.lower()
    if "long form" in lowered:
        return SCREEN_LABEL_FILM
    if "short form" in lowered:
        return SCREEN_LABEL_TV_EPISODE
    return MEDIUM_SCREEN


def is_short_fiction_category(category: str) -> bool:
    """Return True when ``category`` is short story / novelette / short fiction.

    Excludes Best Editor Short Form, Dramatic Presentation Short Form, and
    non-fiction short labels.

    Args:
        category: Award / list section label from a Living List member.

    Returns:
        True for short-fiction Living List categories.
    """
    lowered = category.lower()
    if "dramatic presentation" in lowered:
        return False
    if "editor" in lowered and "short" in lowered:
        return False
    if "non-fiction" in lowered or "nonfiction" in lowered:
        return False
    if "novelette" in lowered:
        return True
    if "short story" in lowered or "short stories" in lowered:
        return True
    if "short fiction" in lowered or "shorter fiction" in lowered:
        return True
    return False


def list_active_finding_records(cache_dir: Path) -> list[dict[str, Any]]:
    """Load every active Finding JSON under ``cache_dir``.

    Active files are ``{finding_id}.json`` whose on-disk name matches the
    record's ``finding_id``. Archive supersedes (``{finding_id}.{stamp}.json``)
    are skipped.

    Args:
        cache_dir: Finding cache directory (usually repo ``findings/``).

    Returns:
        Finding records sorted by ``finding_id``.
    """
    if not cache_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(cache_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        finding_id = data.get("finding_id")
        if not isinstance(finding_id, str):
            continue
        if path.name != f"{finding_id}.json":
            continue
        records.append(data)
    records.sort(key=lambda r: str(r["finding_id"]))
    return records


def recommend_pull(
    *,
    cache_dir: Path,
    grilling_record: Path,
    medium: str = MEDIUM_BOOKS,
    required_finding_ids: Sequence[str] | None = None,
    candidate_work_ids: Sequence[str] = (),
    now: datetime | None = None,
) -> RecommendPullResult:
    """Load active Findings, run the Evidence gate, and collect members by medium.

    Args:
        cache_dir: Finding cache directory.
        grilling_record: Path to ``taste/grilling-record.md`` (or a fixture).
        medium: ``books`` (default novel/novella), ``screen`` (Dramatic
            Presentation), or ``short`` (short story / novelette / short fiction).
        required_finding_ids: Finding ids that must be present. Defaults to every
            loaded active finding id (Living List lane fail-closed).
        candidate_work_ids: Extra Stable Work ids for the spoiler map.
        now: Evaluation instant (defaults to UTC now). Prefer injecting in tests.

    Returns:
        A :class:`RecommendPullResult` with gate fields and medium members.

    Raises:
        ValueError: If ``medium`` is not a supported value.
    """
    if medium not in VALID_MEDIA:
        raise ValueError(
            f"unsupported medium {medium!r}; expected one of "
            f"{sorted(VALID_MEDIA)}"
        )
    records = list_active_finding_records(cache_dir)
    finding_ids = tuple(str(r["finding_id"]) for r in records)
    required = (
        tuple(required_finding_ids)
        if required_finding_ids is not None
        else finding_ids
    )
    certainty = load_certainty_map(grilling_record)
    gate_findings = tuple(to_gate_finding(r) for r in records)
    gate: GateResult = evaluate(
        certainty=certainty,
        findings=gate_findings,
        required_finding_ids=required,
        candidate_work_ids=candidate_work_ids,
        now=now,
    )
    members = _collect_members(records, medium=medium)
    return RecommendPullResult(
        decision=gate.decision.value if records else "clarify-or-refuse",
        refresh_suggested=gate.refresh_suggested,
        missing_required_finding_ids=gate.missing_required_finding_ids,
        blocked_finding_ids=gate.blocked_finding_ids,
        finding_ids=finding_ids,
        medium=medium,
        members=members,
        spoiler_allowed=dict(gate.spoiler_allowed),
    )


def format_pull_report(result: RecommendPullResult) -> str:
    """Format a recommend pull result as agent-readable plain text.

    Args:
        result: Outcome from :func:`recommend_pull`.

    Returns:
        Multi-line report including gate decision, medium, and members.
    """
    hint = _medium_hint(result.medium)
    lines = [
        f"decision: {result.decision}",
        f"refresh_suggested: {str(result.refresh_suggested).lower()}",
        f"missing_required_finding_ids: {_format_id_list(result.missing_required_finding_ids)}",
        f"blocked_finding_ids: {_format_id_list(result.blocked_finding_ids)}",
        f"findings_loaded: {_format_id_list(result.finding_ids)}",
        f"medium: {result.medium}",
        f"members ({hint}): {len(result.members)}",
    ]
    for member in result.members:
        lines.append(
            f"- [{member['finding_id']}] {member['title']} — {member['creator']} "
            f"({member['category']}, {member['year']}) [{member['medium']}]"
        )
    return "\n".join(lines) + "\n"


_MEDIUM_HINTS: Mapping[str, str] = {
    MEDIUM_BOOKS: BOOKISH_CATEGORY_HINT,
    MEDIUM_SCREEN: SCREEN_CATEGORY_HINT,
    MEDIUM_SHORT: SHORT_CATEGORY_HINT,
}

_MEDIUM_PREDICATES: Mapping[str, Callable[[str], bool]] = {
    MEDIUM_BOOKS: is_novel_or_novella_category,
    MEDIUM_SCREEN: is_screen_category,
    MEDIUM_SHORT: is_short_fiction_category,
}


def _medium_hint(medium: str) -> str:
    return _MEDIUM_HINTS.get(medium, BOOKISH_CATEGORY_HINT)


def _category_predicate(medium: str) -> Callable[[str], bool]:
    return _MEDIUM_PREDICATES.get(medium, is_novel_or_novella_category)


def _member_medium_label(*, pull_medium: str, category: str) -> str:
    """Per-member medium tag for reports (screen form when distinguishable)."""
    if pull_medium == MEDIUM_SCREEN:
        return screen_form_label(category)
    return pull_medium


def _collect_members(
    records: Sequence[Mapping[str, Any]],
    *,
    medium: str,
) -> tuple[dict[str, Any], ...]:
    """Extract Living List members matching the requested medium."""
    matches = _category_predicate(medium)
    members: list[dict[str, Any]] = []
    for record in records:
        if str(record.get("kind")) != "living_list":
            continue
        finding_id = str(record["finding_id"])
        payload = record.get("payload") or {}
        raw_members = payload.get("members") or []
        if not isinstance(raw_members, list):
            continue
        for raw in raw_members:
            if not isinstance(raw, Mapping):
                continue
            category = str(raw.get("category", ""))
            if not matches(category):
                continue
            members.append(
                {
                    "finding_id": finding_id,
                    "title": str(raw.get("title", "")),
                    "creator": str(raw.get("creator", "")),
                    "category": category,
                    "year": raw.get("year"),
                    "medium": _member_medium_label(
                        pull_medium=medium, category=category
                    ),
                }
            )
    return tuple(members)


def _format_id_list(ids: Sequence[str]) -> str:
    if not ids:
        return "(none)"
    return ", ".join(ids)
