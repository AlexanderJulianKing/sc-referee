from __future__ import annotations

import functools
import json
import runpy
import shutil
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_4 import (
    ADMISSION_KINDS,
    admission_census,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v34,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_4/prototype-sweep").resolve()
_E17 = Path("evaluation/development/blind-envelope-17-2026-08-30")
_MOVERS = {
    "a2e031f79e31c80fd900": ["candidate", "none"],
    "b4e507c4b55954752f14": ["candidate", "strict_subset"],
}
_MOVEMENT_KEYS = (
    "E17:P3:a2e031f79e31c80fd900",
    "E17:P6:b4e507c4b55954752f14",
)

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_ALL_CASES = cast(Callable[[], tuple[Any, ...]], _harness["all_cases"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _harness["classify"])
_OUTCOME_FROM_JSON = cast(Callable[[list[object]], Any], _harness["outcome_from_json"])
_CURRENT_QUESTION_KEYS = cast(Callable[[], frozenset[str]], _harness["current_question_keys"])
_ADAPTER_SHORT_CIRCUIT = cast(frozenset[str], _harness["ADAPTER_SHORT_CIRCUIT"])
_RESULTS = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
_PROTOTYPE_CASE_ROWS = {row["key"]: row for row in _RESULTS["cases"]}


@functools.cache
def _e17_cases() -> tuple[Any, ...]:
    """The fifteen E17 cases, resolved once per process on first use rather than at import.

    `all_cases` baselines all 170 evidence sources through the shipped 3.3 analyzer and anchors
    each against the frozen 3.3 prototype row.  That work is unchanged; it now runs when a test
    first asks for a case instead of while pytest is collecting this file.
    """

    return tuple(case for case in _ALL_CASES() if case.envelope == "E17")


def _baseline(case: Any) -> list[str]:
    return [case.baseline.state, case.baseline.reason_or_classification]


@pytest.fixture(scope="session")
def executed_case_rows() -> dict[str, dict[str, Any]]:
    """Execute all 170 evidence sources through the real shipped 3.4 analyzer."""

    rows: dict[str, dict[str, Any]] = {}
    for case in _ALL_CASES():
        values = _INPUTS(case, None)
        content = cast(bytes, values.pop("content"))
        with recording_admissions():
            result = analyze_v34(content, **values)
            census = admission_census()
        outcome = _CLASSIFY(result)
        rows[case.key] = {
            "case": case,
            "outcome": outcome,
            "json": outcome.as_json(),
            "census": census,
        }
    return rows


@pytest.fixture(scope="session")
def e17_adapter_rows(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Run the real development-lane adapter and controller over all fifteen E17 cases."""

    adapter = cast(
        Callable[[Path, bytes], dict[str, Any]],
        runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")[
            "adapter_envelope"
        ],
    )
    staging = tmp_path_factory.mktemp("mt34-e17-adapter")
    rows: dict[str, dict[str, Any]] = {}
    for row in _e17_cases():
        case_id = str(row.key.rsplit(":", 1)[-1])
        source = _E17 / "cases" / case_id
        case = staging / case_id
        case.mkdir()
        shutil.copytree(source / "project", case / "project")
        shutil.copy2(source / "profile_1_2_0.json", case / "profile_1_2_0.json")
        (case / "PROMPT.txt").write_text("Static scientific audit.\n", encoding="utf-8")
        rows[case_id] = adapter(case, (case / "project/analysis.py").read_bytes())
    assert len(rows) == 15
    return rows


def test_e17_adapter_oracle_and_exact_movement_set(
    e17_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    """Both pinned movements are re-demonstrated through the real adapter/controller path."""

    movements: set[str] = set()
    for row in _e17_cases():
        case_id = str(row.key.rsplit(":", 1)[-1])
        expected = _MOVERS.get(case_id, _baseline(row))
        actual = e17_adapter_rows[case_id]
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != _baseline(row):
            movements.add(case_id)
    assert movements == set(_MOVERS)
    p3 = e17_adapter_rows["a2e031f79e31c80fd900"]
    assert p3["authorized_count"] == 6
    assert p3["corrected_positions"] == []
    assert p3["candidate_records"] == 1
    p6 = e17_adapter_rows["b4e507c4b55954752f14"]
    assert p6["authorized_count"] == 7
    assert p6["corrected_positions"] == [0, 1, 2]
    assert p6["candidate_records"] == 1
    # The nine E17 negatives stay noncandidates at the adapter level.
    for row in _e17_cases():
        if row.role.startswith("N"):
            case_id = str(row.key.rsplit(":", 1)[-1])
            assert e17_adapter_rows[case_id]["outcome"][0] == "abstain", case_id


def test_all_170_source_rows_match_the_pinned_executed_oracle(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    for key, row in executed_case_rows.items():
        prototype = _PROTOTYPE_CASE_ROWS[key]
        pinned = _OUTCOME_FROM_JSON(
            prototype["outcome"] if prototype["changed"] else prototype["source_analyzer_baseline"]
        )
        value = row["outcome"]
        assert value.state == pinned.state, key
        assert value.reason_or_classification == pinned.reason_or_classification, key
        assert value.corrected_positions == pinned.corrected_positions, key
        if pinned.authorized_count is not None:
            assert value.authorized_count == pinned.authorized_count, key


def test_the_movement_set_is_exactly_the_two_pinned_e17_rows(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    movements = tuple(
        key
        for key, row in executed_case_rows.items()
        if key not in _ADAPTER_SHORT_CIRCUIT and row["outcome"] != row["case"].baseline
    )
    assert movements == _MOVEMENT_KEYS
    assert executed_case_rows[_MOVEMENT_KEYS[0]]["json"] == [
        "candidate",
        "none",
        {"authorized_count": 6, "corrected_positions": []},
    ]
    assert executed_case_rows[_MOVEMENT_KEYS[1]]["json"] == [
        "candidate",
        "strict_subset",
        {"authorized_count": 7, "corrected_positions": [0, 1, 2]},
    ]
    lost = [
        key
        for key, row in executed_case_rows.items()
        if row["case"].baseline.state in {"candidate", "covered"}
        and row["outcome"] != row["case"].baseline
    ]
    assert lost == []


def test_all_105_e10_to_e16_rows_and_all_50_corpus_rows_are_byte_identical(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    moved = [
        key
        for key, row in executed_case_rows.items()
        if row["case"].envelope != "E17"
        and key not in _ADAPTER_SHORT_CIRCUIT
        and row["outcome"] != row["case"].baseline
    ]
    assert moved == []
    assert (
        sum(row["case"].envelope not in {None, "E17"} for row in executed_case_rows.values()) == 105
    )
    assert sum(row["case"].envelope is None for row in executed_case_rows.values()) == 50


@pytest.mark.parametrize("key", sorted(_ADAPTER_SHORT_CIRCUIT))
def test_no_admission_crosses_an_adapter_short_circuit(
    key: str, executed_case_rows: dict[str, dict[str, Any]]
) -> None:
    """E10 N7 and corpus spec-30 resolve at adapter level before the source analyzer."""

    row = executed_case_rows[key]
    prototype = _PROTOTYPE_CASE_ROWS[key]
    assert prototype["adapter_short_circuit"] is True
    assert row["json"] == prototype["source_analyzer_baseline"]
    assert row["census"] == dict.fromkeys(ADMISSION_KINDS, 0)


def test_none_flip_populations_and_retro_recall_are_exact(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    opened = [row for row in executed_case_rows.values() if row["case"].envelope is not None]
    corpus = [row for row in executed_case_rows.values() if row["case"].envelope is None]
    opened_negatives = [row for row in opened if row["case"].designed_class == "negative"]
    corpus_correct = [row for row in corpus if row["case"].designed_class == "correct"]
    corpus_misstep = [row for row in corpus if row["case"].designed_class == "misstep"]
    assert len(opened_negatives) == 72
    assert len(corpus_correct) == 25
    assert len(corpus_misstep) == 25
    assert sum(row["json"][0] == "candidate" for row in opened_negatives) == 0
    assert sum(row["json"][0] == "candidate" for row in corpus_correct) == 0
    assert sum(row["json"][0] == "candidate" for row in corpus_misstep) == 19

    retro = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17"):
        positives = [
            row
            for row in opened
            if row["case"].envelope == envelope and row["case"].role.startswith("P")
        ]
        retro[envelope] = f"{sum(row['json'][0] == 'candidate' for row in positives)}/6"
    assert retro == {
        "E10": "5/6",
        "E11": "6/6",
        "E12": "6/6",
        "E13": "4/6",
        "E14": "4/6",
        "E15": "3/6",
        "E16": "4/6",
        "E17": "6/6",
    }


def test_admission_census_over_the_170_evidence_rows_is_exact(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    rows = {
        kind: sorted(key for key, row in executed_case_rows.items() if row["census"][kind])
        for kind in ADMISSION_KINDS
    }
    assert rows == {
        "cap": ["E17:P6:b4e507c4b55954752f14"],
        "comprehension": ["E17:P3:a2e031f79e31c80fd900", "corpus:spec-37"],
        "enumerate": ["E17:P6:b4e507c4b55954752f14"],
        "terminal-ifexp": [],
    }
    assert executed_case_rows["corpus:spec-37"]["json"][0] != "candidate"


def test_the_question_census_moves_from_28_to_27_removing_only_e17_p6(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    before = _CURRENT_QUESTION_KEYS()
    after = frozenset(
        key
        for key in before
        if key not in executed_case_rows
        or executed_case_rows[key]["json"][0] not in {"candidate", "covered"}
    )
    assert {
        "opened": sum(not key.startswith("corpus:") for key in before),
        "corpus": sum(key.startswith("corpus:") for key in before),
        "total": len(before),
    } == {"opened": 19, "corpus": 9, "total": 28}
    assert {
        "opened": sum(not key.startswith("corpus:") for key in after),
        "corpus": sum(key.startswith("corpus:") for key in after),
        "total": len(after),
    } == {"opened": 18, "corpus": 9, "total": 27}
    assert sorted(before - after) == ["E17:P6:b4e507c4b55954752f14"]
    assert _RESULTS["question_census"]["removed"] == ["E17:P6:b4e507c4b55954752f14"]


def test_sealed_envelope_17_bytes_and_scoring_are_untouched() -> None:
    """The two retro candidates are development evidence; sealed E17 stays 4/6."""

    audit = json.loads((_E17 / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    role_map = json.loads((_E17 / "ROLE_MAP.json").read_text(encoding="utf-8"))
    assert len(role_map["case_roles_in_fixed_order"]) == 15
    assert audit["first_contact_recall"].startswith("4/6")
    assert set(audit["positive_misses"]) == {"P3", "P6"}
    assert audit["hard_stops"]["negative_candidates"].endswith("PASS")
    assert audit["hard_stops"]["findings_anywhere"] == "0 PASS (30 bundles)"
    assert audit["hard_stops"]["replay"].startswith("15/15")
    assert audit["class_tally"] == (
        "window E17 = 4/6; promotion needs E17+E18 >= 7/12, so E18 needs >= 3/6"
    )
