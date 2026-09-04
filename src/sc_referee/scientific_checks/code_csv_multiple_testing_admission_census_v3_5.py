"""Executed admission census for the multiple-testing 3.5 recall-delta admissions.

The census records, per analyzer call, the exact source span at which each shipped 3.5
production fired.  It exists so a disqualifier fixture can assert that its named production
**did not fire at all**, rather than asserting only that the case abstained: an abstention can
be produced by an unrelated upstream refusal, an empty census cannot.

The census never participates in a proof.  Nothing reads it back to decide a classification, a
position, a reason, or a record; recording is write-only from the recognizers' point of view.
D2 (`d2-set-selector`) and D3 (`d3-csv-reader`) are specified in the 3.5 design and are **not**
installed, so their kinds are present and permanently empty.

The 3.4 census is a separate module and is untouched, so a 3.5 run can open both without
either count being shared.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sc_referee.core.ids import sha256_digest

CODE_CSV_MULTIPLE_TESTING_ADMISSION_CENSUS_V3_5_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

#: The six 3.5 production slots.  `d2-set-selector` and `d3-csv-reader` are specified and not
#: installed, so nothing can record against them.
ADMISSION_KINDS: tuple[str, ...] = (
    "d1-format-arm",
    "d2-set-selector",
    "d3-csv-reader",
    "d4a-numeric-group",
    "d4b-loop-terminal",
    "d5-cardinality-read",
)

#: The three shipped groups.  D4a and D4b ship as a pair; D4a alone reaches only a different
#: abstention, which the ordering rule turns into no public change at all.
INSTALLED_KINDS: tuple[str, ...] = (
    "d1-format-arm",
    "d4a-numeric-group",
    "d4b-loop-terminal",
    "d5-cardinality-read",
)

_SPANS: dict[str, set[tuple[int, int, int, int]]] = {kind: set() for kind in ADMISSION_KINDS}
_ACTIVE = False


def record_admission(kind: str, span: tuple[int, int, int, int]) -> None:
    """Record one admitted span.  Ignored unless a census is open."""

    if kind not in _SPANS:
        raise ValueError(f"unknown multiple-testing 3.5 admission kind: {kind}")
    if kind not in INSTALLED_KINDS:
        raise ValueError(f"multiple-testing 3.5 production {kind} is not installed")
    if _ACTIVE:
        _SPANS[kind].add(span)


def admission_census() -> dict[str, int]:
    """The span count for each production kind recorded since the census opened."""

    return {kind: len(_SPANS[kind]) for kind in ADMISSION_KINDS}


def admission_spans() -> dict[str, tuple[tuple[int, int, int, int], ...]]:
    """The recorded spans themselves, sorted, for evidence and diagnostics."""

    return {kind: tuple(sorted(_SPANS[kind])) for kind in ADMISSION_KINDS}


@contextmanager
def recording_admissions() -> Iterator[None]:
    """Open one census.  Nested use is refused so a count is never silently shared."""

    global _ACTIVE
    if _ACTIVE:
        raise RuntimeError("the multiple-testing 3.5 admission census is already recording")
    for spans in _SPANS.values():
        spans.clear()
    _ACTIVE = True
    try:
        yield
    finally:
        _ACTIVE = False


__all__ = [
    "ADMISSION_KINDS",
    "CODE_CSV_MULTIPLE_TESTING_ADMISSION_CENSUS_V3_5_IMPLEMENTATION_DIGEST",
    "INSTALLED_KINDS",
    "admission_census",
    "admission_spans",
    "record_admission",
    "recording_admissions",
]
