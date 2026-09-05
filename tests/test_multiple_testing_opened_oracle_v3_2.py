from __future__ import annotations

import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

_ROOT = Path("evaluation/development/blind-envelope-15-2026-08-29")
_AUDIT = json.loads((_ROOT / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_ADAPTER = cast(Callable[[Path, bytes], dict[str, Any]], _HARNESS["adapter_envelope"])
_MOVER = "81980e878c1bc8cc216b"
#: MT 3.5 movement, re-pointed in fix round 2.  E15 P3 is one of the four rows the shipped 3.5
#: lane moves: the correction it recognised is dead, so the family is uncorrected and the row is
#: a true accusation rather than the frozen 3.2 consumption abstention.  It is a positive case,
#: so E15 retro recall rises from three of six to four of six; no negative moved.
_V35_MOVER = "afe47b2a7ea87ed21a69"
_V35_MOVER_OUTCOME = ["candidate", "none"]


def _baseline(row: dict[str, Any]) -> list[str]:
    if row["dev_outcome"] == "abstain":
        return ["abstain", str(row["dev_reason_or_classification"])]
    if row["dev_outcome"] == "candidate":
        return ["candidate", str(row["dev_reason_or_classification"])]
    assert row["dev_outcome"] == "covered_complete"
    return ["covered", "complete"]


@pytest.fixture(scope="module")
def e15_adapter_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for metadata in _AUDIT["cases"]:
        case_id = str(metadata["case_id"])
        case = _ROOT / "cases" / case_id
        rows[case_id] = _ADAPTER(case, (case / "project/analysis.py").read_bytes())
    assert len(rows) == 15
    return rows


def test_final_adapter_movement_set_is_exact(
    e15_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    movements: set[str] = set()
    for metadata in _AUDIT["cases"]:
        case_id = str(metadata["case_id"])
        actual = e15_adapter_rows[case_id]
        baseline = _baseline(metadata)
        if case_id == _MOVER:
            expected = ["candidate", "strict_subset"]
        elif case_id == _V35_MOVER:
            expected = _V35_MOVER_OUTCOME
        else:
            expected = baseline
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != baseline:
            movements.add(case_id)
    assert movements == {_MOVER, _V35_MOVER}


def test_e15_p6_and_complete_control_are_exact(
    e15_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    mover = e15_adapter_rows[_MOVER]
    assert mover["outcome"] == ["candidate", "strict_subset"]
    assert mover["corrected_positions"] == [0, 1, 3]
    assert mover["authorized_count"] == 8
    assert mover["candidate_records"] == 1
    assert mover["finding_count"] == 0

    complete = e15_adapter_rows["f846b07b1d11131cec4d"]
    assert complete["outcome"] == ["covered", "complete"]
    assert complete["corrected_positions"] == [0, 1, 2, 3]
    assert complete["authorized_count"] == 4
    assert complete["candidate_records"] == 0
    assert complete["finding_count"] == 0


def test_e15_retro_recall_and_negative_none_flip(
    e15_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    positives = [row for row in _AUDIT["cases"] if row["role"].startswith("P")]
    negatives = [row for row in _AUDIT["cases"] if row["designed_class"] == "negative"]
    # Three under 3.2, four since the 3.5 lane moved E15 P3 (`_V35_MOVER`) to candidate/none.
    assert (
        sum(e15_adapter_rows[str(row["case_id"])]["outcome"][0] == "candidate" for row in positives)
        == 4
    )
    assert len(negatives) == 9
    assert not [
        row["case_id"]
        for row in negatives
        if e15_adapter_rows[str(row["case_id"])]["outcome"][0] == "candidate"
    ]
