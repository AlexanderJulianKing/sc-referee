"""Executed admission census for the multiple-testing 3.4 syntactic admissions.

The census records, per analyzer call, the exact source span at which each shipped 3.4
admission fired.  It exists so a disqualifier fixture can assert that its named admission
**did not fire at all**, rather than asserting only that the case abstained: an abstention
can be produced by an unrelated upstream refusal, an empty census cannot.

The census never participates in a proof.  Nothing reads it back to decide a classification,
a position, a reason, or a record; recording is write-only from the recognizers' point of
view.  Extension B (the terminal `IfExp` print-only production) is specified in the 3.4 design
and is **not** shipped, so its kind is present and permanently empty.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sc_referee.core.ids import sha256_digest

CODE_CSV_MULTIPLE_TESTING_ADMISSION_CENSUS_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

#: The four 3.4 extension slots.  `terminal-ifexp` is specified and not shipped.
ADMISSION_KINDS: tuple[str, ...] = ("cap", "comprehension", "enumerate", "terminal-ifexp")

_SPANS: dict[str, set[tuple[int, int, int, int]]] = {kind: set() for kind in ADMISSION_KINDS}
_ACTIVE = False


def record_admission(kind: str, span: tuple[int, int, int, int]) -> None:
    """Record one admitted span.  Ignored unless a census is open."""

    if kind not in _SPANS:
        raise ValueError(f"unknown multiple-testing 3.4 admission kind: {kind}")
    if _ACTIVE:
        _SPANS[kind].add(span)


def admission_census() -> dict[str, int]:
    """The span count for each admission kind recorded since the census opened."""

    return {kind: len(_SPANS[kind]) for kind in ADMISSION_KINDS}


def admission_spans() -> dict[str, tuple[tuple[int, int, int, int], ...]]:
    """The recorded spans themselves, sorted, for evidence and diagnostics."""

    return {kind: tuple(sorted(_SPANS[kind])) for kind in ADMISSION_KINDS}


@contextmanager
def recording_admissions() -> Iterator[None]:
    """Open one census.  Nested use is refused so a count is never silently shared."""

    global _ACTIVE
    if _ACTIVE:
        raise RuntimeError("the multiple-testing 3.4 admission census is already recording")
    for spans in _SPANS.values():
        spans.clear()
    _ACTIVE = True
    try:
        yield
    finally:
        _ACTIVE = False


__all__ = [
    "ADMISSION_KINDS",
    "CODE_CSV_MULTIPLE_TESTING_ADMISSION_CENSUS_IMPLEMENTATION_DIGEST",
    "admission_census",
    "admission_spans",
    "record_admission",
    "recording_admissions",
]
