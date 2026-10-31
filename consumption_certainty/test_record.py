"""Behaviour tests for Consumption certainty grilling-record reader seam."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from consumption_certainty.record import (
    certainty_for,
    load_certainty_map,
    read_certainty_map,
    stable_work_id,
)
from evidence_gate.gate import ConsumptionCertainty, evaluate

NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)

SAMPLE_SECTION = """\
# Taste record

## Other stuff

Ignore this.

## Consumption certainty

Queryable per–Stable Work field. Values: `consumed` | `heard-of` | `unknown` | `won't-read`.
Unlisted works default to `unknown`. Per-work only (no series-level Won't-read).

| Title | Creator | Certainty |
| --- | --- | --- |
| Example Novel A | Example Writer A | consumed |
| Unopened Volume | Example Writer B | won't-read |
| Example Novel D | Example Writer D | won't-read |
| Example Novel C | Example Writer C | heard-of |
| Example Novel E | Example Writer E | consumed |

## Session addenda

Later notes go here.
"""


def test_read_certainty_map_parses_four_glossary_states() -> None:
    certainty = read_certainty_map(SAMPLE_SECTION)

    assert certainty[stable_work_id("Example Novel A", "Example Writer A")] == (
        ConsumptionCertainty.CONSUMED
    )
    assert certainty[
        stable_work_id("Unopened Volume", "Example Writer B")
    ] == ConsumptionCertainty.WONT_READ
    assert certainty[stable_work_id("Example Novel D", "Example Writer D")] == (
        ConsumptionCertainty.WONT_READ
    )
    assert certainty[stable_work_id("Example Novel C", "Example Writer C")] == (
        ConsumptionCertainty.HEARD_OF
    )


def test_certainty_for_defaults_missing_works_to_unknown() -> None:
    certainty = read_certainty_map(SAMPLE_SECTION)

    assert (
        certainty_for(certainty, stable_work_id("Unknown Novel", "A. Author"))
        is ConsumptionCertainty.UNKNOWN
    )


def test_reader_map_feeds_evidence_gate_spoiler_permission() -> None:
    certainty = read_certainty_map(SAMPLE_SECTION)
    consumed = stable_work_id("Example Novel A", "Example Writer A")
    skipped = stable_work_id(
        "Unopened Volume", "Example Writer B"
    )
    heard = stable_work_id("Example Novel C", "Example Writer C")
    unseen = stable_work_id("Example Novel F", "Example Writer F")

    result = evaluate(
        certainty=certainty,
        findings=(),
        candidate_work_ids=(consumed, skipped, heard, unseen),
        now=NOW,
    )

    assert result.spoiler_allowed[consumed] is True
    assert result.spoiler_allowed[skipped] is True
    assert result.spoiler_allowed[heard] is False
    assert result.spoiler_allowed[unseen] is False


def test_invalid_certainty_value_is_treated_as_unknown() -> None:
    markdown = """\
## Consumption certainty

| Title | Creator | Certainty |
| --- | --- | --- |
| Bad Entry | A. Author | maybe-read |
"""
    certainty = read_certainty_map(markdown)
    work = stable_work_id("Bad Entry", "A. Author")
    assert certainty[work] is ConsumptionCertainty.UNKNOWN


def test_missing_section_yields_empty_map() -> None:
    assert read_certainty_map("# No certainty here\n") == {}


def test_load_certainty_map_reads_grilling_record_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "grilling-record.md"
    path.write_text(SAMPLE_SECTION, encoding="utf-8")

    certainty = load_certainty_map(path)
    assert certainty[stable_work_id("Example Novel A", "Example Writer A")] is (
        ConsumptionCertainty.CONSUMED
    )
