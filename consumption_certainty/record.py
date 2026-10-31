"""Read Consumption certainty from the grilling record for the Evidence gate."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from evidence_gate.gate import ConsumptionCertainty

_SECTION_HEADING = "## Consumption certainty"
_VALID = {c.value: c for c in ConsumptionCertainty}
_WORK_ID_SEP = " — "


def stable_work_id(title: str, creator: str) -> str:
    """Build the Stable Work id used as the certainty map key.

    Args:
        title: Work title (as recorded in the grilling-record table).
        creator: Creator name (as recorded in the grilling-record table).

    Returns:
        Canonical id ``"{title} — {creator}"`` with surrounding whitespace stripped.
    """
    return f"{title.strip()}{_WORK_ID_SEP}{creator.strip()}"


def certainty_for(
    certainty: Mapping[str, str | ConsumptionCertainty],
    work_id: str,
) -> ConsumptionCertainty:
    """Return Consumption certainty for a Stable Work, defaulting to unknown.

    Args:
        certainty: Map from Stable Work id to certainty value or enum.
        work_id: Stable Work id (see :func:`stable_work_id`).

    Returns:
        The recorded certainty, or :attr:`ConsumptionCertainty.UNKNOWN` when
        the work is absent or the stored value is not one of the four glossary
        states.
    """
    if work_id not in certainty:
        return ConsumptionCertainty.UNKNOWN
    return _normalize(certainty[work_id])


def read_certainty_map(markdown: str) -> dict[str, ConsumptionCertainty]:
    """Parse the Consumption certainty section of a grilling-record markdown body.

    Expects a ``## Consumption certainty`` heading and a markdown table with
    columns ``Title``, ``Creator``, and ``Certainty``. Rows with invalid
    certainty values are stored as ``unknown``. Works not listed are omitted;
    callers should treat omission as ``unknown`` via :func:`certainty_for` or
    the Evidence gate.

    Args:
        markdown: Full grilling-record markdown (or a fragment containing the
            section).

    Returns:
        Mapping of Stable Work id to :class:`ConsumptionCertainty`. Empty when
        the section is missing.
    """
    section = _extract_section(markdown)
    if section is None:
        return {}

    rows = _parse_table_rows(section)
    result: dict[str, ConsumptionCertainty] = {}
    for title, creator, value in rows:
        result[stable_work_id(title, creator)] = _normalize(value)
    return result


def load_certainty_map(path: str | Path) -> dict[str, ConsumptionCertainty]:
    """Load and parse Consumption certainty from a grilling-record file.

    Args:
        path: Path to ``taste/grilling-record.md`` (or a test fixture).

    Returns:
        Mapping of Stable Work id to :class:`ConsumptionCertainty`.
    """
    text = Path(path).read_text(encoding="utf-8")
    return read_certainty_map(text)


def _normalize(value: str | ConsumptionCertainty) -> ConsumptionCertainty:
    if isinstance(value, ConsumptionCertainty):
        return value
    return _VALID.get(value.strip(), ConsumptionCertainty.UNKNOWN)


def _extract_section(markdown: str) -> str | None:
    lines = markdown.splitlines()
    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == _SECTION_HEADING:
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            end = i
            break
    return "\n".join(lines[start:end])


def _parse_table_rows(section: str) -> list[tuple[str, str, str]]:
    """Extract (title, creator, certainty) rows from a markdown table."""
    rows: list[tuple[str, str, str]] = []
    header_seen = False
    title_i = creator_i = certainty_i = -1

    for raw in section.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        if all(set(c) <= {"-", ":"} and c for c in cells):
            continue
        if not header_seen:
            lower = [c.casefold() for c in cells]
            try:
                title_i = lower.index("title")
                creator_i = lower.index("creator")
                certainty_i = lower.index("certainty")
            except ValueError:
                continue
            header_seen = True
            continue
        if title_i < 0 or max(title_i, creator_i, certainty_i) >= len(cells):
            continue
        title, creator, value = (
            cells[title_i],
            cells[creator_i],
            cells[certainty_i],
        )
        if title and creator and value:
            rows.append((title, creator, value))
    return rows
