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
        expected = ["candidate", "strict_subset"] if case_id == _MOVER else baseline
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != baseline:
            movements.add(case_id)
    assert movements == {_MOVER}


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
    assert (
        sum(e15_adapter_rows[str(row["case_id"])]["outcome"][0] == "candidate" for row in positives)
        == 3
    )
    assert len(negatives) == 9
    assert not [
        row["case_id"]
        for row in negatives
        if e15_adapter_rows[str(row["case_id"])]["outcome"][0] == "candidate"
    ]
