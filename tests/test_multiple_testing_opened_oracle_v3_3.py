from __future__ import annotations

import json
import runpy
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_3/prototype-sweep").resolve()
_E16 = Path("evaluation/development/blind-envelope-16-2026-08-30")
_MOVERS = {
    "7a43fa7b50f1b99e5034": ["candidate", "none"],
    "5a9c5b4377c33916d672": ["candidate", "none"],
    "9ced761b41ef93485acf": ["candidate", "none"],
}

sys.path.insert(0, str(_ROOT))
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
finally:
    sys.path.remove(str(_ROOT))

_ALL_CASES = cast(Callable[[], tuple[Any, ...]], _harness["all_cases"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _harness["classify"])
_OUTCOME_FROM_JSON = cast(Callable[[list[object]], Any], _harness["outcome_from_json"])
_E16_CASES = tuple(case for case in _ALL_CASES() if case.envelope == "E16")


def _baseline(case: Any) -> list[str]:
    return [case.baseline.state, case.baseline.reason_or_classification]


@pytest.fixture(scope="module")
def e16_adapter_rows(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    adapter = cast(
        Callable[[Path, bytes], dict[str, Any]],
        runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")[
            "adapter_envelope"
        ],
    )
    staging = tmp_path_factory.mktemp("mt33-e16-adapter")
    rows: dict[str, dict[str, Any]] = {}
    for row in _E16_CASES:
        case_id = str(row.key.rsplit(":", 1)[-1])
        source = _E16 / "cases" / case_id
        case = staging / case_id
        case.mkdir()
        shutil.copytree(source / "project", case / "project")
        shutil.copy2(source / "profile_1_2_0.json", case / "profile_1_2_0.json")
        (case / "PROMPT.txt").write_text("Static scientific audit.\n", encoding="utf-8")
        rows[case_id] = adapter(case, (case / "project/analysis.py").read_bytes())
    assert len(rows) == 15
    return rows


def test_e16_adapter_oracle_and_exact_movement_set(
    e16_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    movements: set[str] = set()
    for row in _E16_CASES:
        case_id = str(row.key.rsplit(":", 1)[-1])
        expected = _MOVERS.get(case_id, _baseline(row))
        actual = e16_adapter_rows[case_id]
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != _baseline(row):
            movements.add(case_id)
    assert movements == set(_MOVERS)
    for case_id, count in {
        "7a43fa7b50f1b99e5034": 6,
        "5a9c5b4377c33916d672": 5,
        "9ced761b41ef93485acf": 7,
    }.items():
        assert e16_adapter_rows[case_id]["authorized_count"] == count
        assert e16_adapter_rows[case_id]["candidate_records"] == 1
    assert e16_adapter_rows["76f0e7831f3856df66d5"]["outcome"] == ["covered", "complete"]
    assert e16_adapter_rows["76f0e7831f3856df66d5"]["corrected_positions"] == [0, 1, 2, 3, 4]


def test_all_155_source_rows_match_the_pinned_executed_oracle() -> None:
    payload = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
    expected = {
        row["key"]: _OUTCOME_FROM_JSON(
            row["outcome"] if row["changed"] else row["source_analyzer_baseline"]
        )
        for row in payload["cases"]
    }
    actual: dict[str, Any] = {}
    for case in _ALL_CASES():
        values = _INPUTS(case, None)
        content = cast(bytes, values.pop("content"))
        actual[case.key] = _CLASSIFY(analyze_code_csv_multiple_testing_dataflow(content, **values))
    for key, value in actual.items():
        pinned = expected[key]
        assert value.state == pinned.state, key
        assert value.reason_or_classification == pinned.reason_or_classification, key
        assert value.corrected_positions == pinned.corrected_positions, key
        if pinned.authorized_count is not None:
            assert value.authorized_count == pinned.authorized_count, key


def test_none_flip_retro_and_question_censuses_are_exact() -> None:
    payload = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
    assert payload["none_flip"] == {
        "all_correct_fixtures": [0, 183],
        "ap_correct": [0, 13],
        "b5_expression_variants": [0, 63],
        "corpus_correct": [0, 25],
        "cumulative_v3_correct": [0, 62],
        "frozen_gatekeeping": [0, 12],
        "new_terminal_helper_correct": [0, 17],
        "opened_negatives": [0, 63],
        "v31_laundering_adjacent": [0, 16],
    }
    assert payload["retro_recall"] == {
        "E10": "5/6",
        "E11": "6/6",
        "E12": "6/6",
        "E13": "4/6",
        "E14": "4/6",
        "E15": "3/6",
        "E16": "4/6",
    }
    assert payload["question_census"]["before"] == {"opened": 16, "corpus": 9, "total": 25}
    assert payload["question_census"]["after"] == {"opened": 16, "corpus": 9, "total": 25}
    assert payload["question_census"]["removed"] == []
