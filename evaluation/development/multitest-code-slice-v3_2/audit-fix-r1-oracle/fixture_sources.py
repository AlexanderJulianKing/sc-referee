"""Deterministic source recipes for the independent MT 3.2 audit-fix oracle."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
FIXTURES = REPO / "evaluation/development/multitest-code-slice-v3_2/prototype-sweep/fixtures"


def _replace_once(source: bytes, old: bytes, new: bytes, name: str) -> bytes:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{name}: replacement anchor count is {count}")
    return source.replace(old, new, 1)


def fixture_sources() -> dict[str, tuple[str, bytes]]:
    complete = (FIXTURES / "positive-ap-complete-capped-family-name.py").read_bytes()
    subset = (FIXTURES / "positive-ap-subset-capped-family-name.py").read_bytes()
    threshold = (FIXTURES / "positive-ap-complete-division-threshold.py").read_bytes()
    complete_raw = _replace_once(
        complete,
        b"significant = p_used < ALPHA",
        b"significant = p_raw < ALPHA",
        "complete-raw-consumer",
    )
    subset_raw = _replace_once(
        subset,
        b"significant = p_used < ALPHA",
        b"significant = p_raw < ALPHA",
        "subset-raw-consumer",
    )
    mixed = _replace_once(
        complete,
        b"FAMILY_SIZE = len(OUTCOMES)\n",
        b'FAMILY_SIZE = len(OUTCOMES)\nRAW_VERDICT_OUTCOMES = ["mean_lifespan_d"]\n',
        "mixed-table",
    )
    mixed = _replace_once(
        mixed,
        b"        significant = p_used < ALPHA\n",
        b"        if column in RAW_VERDICT_OUTCOMES:\n"
        b"            significant = p_raw < ALPHA\n"
        b"        else:\n"
        b"            significant = p_used < ALPHA\n",
        "mixed-consumers",
    )
    reject_transport = _replace_once(
        complete,
        b"        significant = p_used < ALPHA\n",
        b"        corrected_reject = p_used < ALPHA\n        significant = corrected_reject\n",
        "reject-transport",
    )
    e15 = "E15:P6:81980e878c1bc8cc216b"
    return {
        "positive-ap-complete-corrected-consumer": (e15, complete),
        "correct-ap-complete-raw-consumer": (e15, complete_raw),
        "positive-ap-subset-corrected-consumer": (e15, subset),
        "correct-ap-subset-raw-consumer": (e15, subset_raw),
        "correct-ap-mixed-corrected-and-raw-consumers": (e15, mixed),
        "positive-ap-complete-reject-flag-transport": (e15, reject_transport),
        "positive-ap-complete-division-threshold-control": ("corpus:spec-28", threshold),
    }


def attestation_fixture_sources() -> dict[str, tuple[str, bytes]]:
    sources = fixture_sources()
    return {
        "controller-answer-b-fails-ap-raw-consumer": sources[
            "correct-ap-mixed-corrected-and-raw-consumers"
        ],
        "answer-removal-equivalence-ap-proving": sources["positive-ap-complete-corrected-consumer"],
        "answer-removal-equivalence-ap-failing": sources[
            "correct-ap-mixed-corrected-and-raw-consumers"
        ],
    }


__all__ = ["attestation_fixture_sources", "fixture_sources"]
