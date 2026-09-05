from __future__ import annotations

import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_0/prototype-sweep")
_RESULTS = json.loads((_SWEEP / "results.json").read_text(encoding="utf-8"))
_HARNESS = runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")
_ADAPTER = cast(Callable[[Path, bytes], dict[str, Any]], _HARNESS["adapter_envelope"])
_INPUTS = cast(Callable[[Path], dict[str, Any]], _HARNESS["envelope_inputs"])
_ROOTS = {
    "E10": Path("evaluation/development/blind-envelope-10-2026-08-24"),
    "E11": Path("evaluation/development/blind-envelope-11-2026-08-25"),
    "E12": Path("evaluation/development/blind-envelope-12-2026-08-26"),
    "E13": Path("evaluation/development/blind-envelope-13-2026-08-26"),
    "E14": Path("evaluation/development/blind-envelope-14-2026-08-27"),
}
_OPENED_ROWS = tuple(row for row in _RESULTS["cases"] if row["envelope"] is not None)
_MOVEMENTS = {
    "E11:P5:114782f595d9c24b923d",
    "E12:P1:f9ce4de5e21d9015ecd9",
    "E12:P5:54667dd7c39067c8c2c8",
    "E12:N1:45c4b9a19d0a630f1cb0",
    "E12:N2:f256af2f5c5d98f37e65",
    "E14:P2:4fc0f5c1ef2d0e2cd5b6",
    "E14:P3:502687d9137dab93ff99",
    "E14:P4:cccde3c60f936e077f80",
    "E14:P5:5e33841b96d85ffe67be",
    "E14:N9:5d5d4e0189d4f2c73f6a",
}
_CANDIDATES = {
    "E11:P5:114782f595d9c24b923d": ("strict_subset", [0, 1], 7),
    "E12:P1:f9ce4de5e21d9015ecd9": ("none", [], 5),
    "E12:P5:54667dd7c39067c8c2c8": ("strict_subset", [0, 1], 7),
    "E14:P2:4fc0f5c1ef2d0e2cd5b6": ("none", [], 6),
    "E14:P4:cccde3c60f936e077f80": ("none", [], 7),
    "E14:P5:5e33841b96d85ffe67be": ("strict_subset", [0, 1], 6),
}


@pytest.fixture(scope="module")
def opened_adapter_rows() -> dict[str, dict[str, Any]]:
    assert len(_OPENED_ROWS) == 75
    observed: dict[str, dict[str, Any]] = {}
    for expected in _OPENED_ROWS:
        envelope, _role, case_id = expected["key"].split(":")
        case = _ROOTS[envelope] / "cases" / case_id
        observed[expected["key"]] = _ADAPTER(
            case,
            (case / "project" / "analysis.py").read_bytes(),
        )
    return observed


def test_all_75_opened_rows_match_the_adapter_oracle(
    opened_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    changed: set[str] = set()
    for expected in _OPENED_ROWS:
        key = expected["key"]
        actual = opened_adapter_rows[key]
        assert actual["outcome"] == expected["outcome"][:2], key
        assert actual["finding_count"] == 0, key
        if expected["outcome"][0] in {"candidate", "covered"}:
            coverage = expected["outcome"][2]
            assert actual["corrected_positions"] == coverage["corrected_positions"], key
            assert actual["authorized_count"] == coverage["authorized_count"], key
        if actual["outcome"] != expected["baseline"][:2]:
            changed.add(key)
    assert changed == _MOVEMENTS


def test_six_candidate_rows_and_complete_control_are_exact(
    opened_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    for key, (classification, positions, count) in _CANDIDATES.items():
        row = opened_adapter_rows[key]
        assert row["outcome"] == ["candidate", classification], key
        assert row["corrected_positions"] == positions, key
        assert row["authorized_count"] == count, key
        assert row["candidate_records"] == 1, key

    complete = opened_adapter_rows["E12:N1:45c4b9a19d0a630f1cb0"]
    assert complete["outcome"] == ["covered", "complete"]
    assert complete["corrected_positions"] == [0, 1, 2, 3, 4]
    assert complete["authorized_count"] == 5
    assert complete["candidate_records"] == 0


def test_retro_recall_and_opened_negative_none_flip_are_exact(
    opened_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    recalls: dict[str, str] = {}
    for envelope in _ROOTS:
        positives = [
            row for row in _OPENED_ROWS if row["envelope"] == envelope and row["role"][0] == "P"
        ]
        caught = sum(
            opened_adapter_rows[row["key"]]["outcome"][0] == "candidate" for row in positives
        )
        recalls[envelope] = f"{caught}/{len(positives)}"
    assert recalls == {"E10": "5/6", "E11": "6/6", "E12": "6/6", "E13": "4/6", "E14": "4/6"}

    negatives = [row for row in _OPENED_ROWS if row["labeled_correct"]]
    assert len(negatives) == 45
    assert not [
        row["key"]
        for row in negatives
        if opened_adapter_rows[row["key"]]["outcome"][0] == "candidate"
    ]


@pytest.mark.parametrize(
    "key",
    [
        "E12:P5:54667dd7c39067c8c2c8",
        "E14:P2:4fc0f5c1ef2d0e2cd5b6",
        "E14:P4:cccde3c60f936e077f80",
        "E14:P5:5e33841b96d85ffe67be",
    ],
)
def test_final_strict_store_movements_carry_per_position_record_and_api_evidence(
    key: str,
) -> None:
    envelope, _role, case_id = key.split(":")
    case = _ROOTS[envelope] / "cases" / case_id
    values = _INPUTS(case)
    content = cast(bytes, values.pop("content"))
    result = analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert result.reason is None
    assert result.facts is not None
    assert len(result.facts.registered_test_apis_by_position) == result.facts.family_size
    assert set(result.facts.registered_test_apis_by_position) <= {
        "scipy.stats.mannwhitneyu",
        "scipy.stats.ttest_ind",
    }
    record_roles = {
        span.role for span in result.facts.evidence_spans if span.role == "record_construction"
    }
    assert record_roles == {"record_construction"}
    if key == "E12:P5:54667dd7c39067c8c2c8":
        assert result.facts.correction_methods == ("holm",)
