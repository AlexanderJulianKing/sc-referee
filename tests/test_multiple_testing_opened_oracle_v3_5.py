"""The 185-row opened oracle for the shipped multiple-testing 3.5 lane.

Every expected row comes from `evaluation/development/multitest-code-slice-v3_5/opened-oracle`,
which is recomputed from the design's own executed sweep rather than from the output of this
build.  The pinned movement set is additionally re-demonstrated through the real
adapter/controller path over all fifteen E18 cases, and the E10 to E17 adapter oracles are
carried forward unchanged.
"""

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

from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
    ADMISSION_KINDS,
    admission_census,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_5 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v35,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_5/prototype-sweep").resolve()
_ORACLE = Path("evaluation/development/multitest-code-slice-v3_5/opened-oracle").resolve()
_E18 = Path("evaluation/development/blind-envelope-18-2026-09-01")
_E17 = Path("evaluation/development/blind-envelope-17-2026-08-30")

_EXPECTED = json.loads((_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_EXPECTED_ROWS = {row["key"]: row for row in _EXPECTED["rows"]}

#: The four pinned movements of design section 3.  Three catches and one true clearance.
_MOVERS: dict[str, list[object]] = {
    "afe47b2a7ea87ed21a69": ["candidate", "none"],
    "e2d8b1bdf4baa671a1b4": ["covered", "complete"],
    "5a9277448db34379ce78": ["candidate", "none"],
    "d1b1fc47ccdabd0c2f22": ["candidate", "none"],
}
_MOVEMENT_KEYS = (
    "E15:P3:afe47b2a7ea87ed21a69",
    "E17:N1:e2d8b1bdf4baa671a1b4",
    "E18:P2:5a9277448db34379ce78",
    "E18:P3:d1b1fc47ccdabd0c2f22",
)
_ADAPTER_SHORT_CIRCUIT = frozenset({"E10:N7:6d2fdc67ab98bc0e0e6e", "corpus:spec-30"})

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_SWEEP / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_ALL_CASES = cast(Callable[[], tuple[Any, ...]], _harness["all_cases"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[Any], Any], _harness["classify"])
_CURRENT_QUESTION_KEYS = cast(Callable[[], frozenset[str]], _harness["current_question_keys"])


@functools.cache
def _envelope_cases(envelope: str) -> tuple[Any, ...]:
    return tuple(case for case in _ALL_CASES() if case.envelope == envelope)


@pytest.fixture(scope="session")
def executed_case_rows() -> dict[str, dict[str, Any]]:
    """Execute all 185 evidence sources through the real shipped 3.5 analyzer."""

    rows: dict[str, dict[str, Any]] = {}
    for case in _ALL_CASES():
        values = _INPUTS(case, None)
        content = cast(bytes, values.pop("content"))
        with recording_admissions():
            result = analyze_v35(content, **values)
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
def e18_adapter_rows(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Run the real development-lane adapter and controller over all fifteen E18 cases."""

    adapter = cast(
        Callable[[Path, bytes], dict[str, Any]],
        runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")[
            "adapter_envelope"
        ],
    )
    staging = tmp_path_factory.mktemp("mt35-e18-adapter")
    rows: dict[str, dict[str, Any]] = {}
    for row in _envelope_cases("E18"):
        case_id = str(row.key.rsplit(":", 1)[-1])
        source = _E18 / "cases" / case_id
        case = staging / case_id
        case.mkdir()
        shutil.copytree(source / "project", case / "project")
        shutil.copy2(source / "profile_1_2_0.json", case / "profile_1_2_0.json")
        (case / "PROMPT.txt").write_text("Static scientific audit.\n", encoding="utf-8")
        rows[case_id] = adapter(case, (case / "project/analysis.py").read_bytes())
    assert len(rows) == 15
    return rows


@pytest.fixture(scope="session")
def e17_adapter_rows(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """The frozen E17 adapter oracle, re-run under 3.5 so its one clearance is visible."""

    adapter = cast(
        Callable[[Path, bytes], dict[str, Any]],
        runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")[
            "adapter_envelope"
        ],
    )
    staging = tmp_path_factory.mktemp("mt35-e17-adapter")
    rows: dict[str, dict[str, Any]] = {}
    for row in _envelope_cases("E17"):
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


def test_e18_adapter_oracle_and_exact_movement_set(
    e18_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    """Both E18 movements are re-demonstrated through the real adapter and controller."""

    movements: set[str] = set()
    for row in _envelope_cases("E18"):
        case_id = str(row.key.rsplit(":", 1)[-1])
        expected = _MOVERS.get(case_id, [row.baseline.state, row.baseline.reason_or_classification])
        actual = e18_adapter_rows[case_id]
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != [row.baseline.state, row.baseline.reason_or_classification]:
            movements.add(case_id)
    assert movements == {"5a9277448db34379ce78", "d1b1fc47ccdabd0c2f22"}
    p2 = e18_adapter_rows["5a9277448db34379ce78"]
    assert p2["authorized_count"] == 6
    assert p2["corrected_positions"] == []
    assert p2["candidate_records"] == 1
    p3 = e18_adapter_rows["d1b1fc47ccdabd0c2f22"]
    assert p3["authorized_count"] == 5
    assert p3["corrected_positions"] == []
    assert p3["candidate_records"] == 1
    # Every E18 negative stays a noncandidate at the adapter level.
    for row in _envelope_cases("E18"):
        if row.role.startswith("N"):
            case_id = str(row.key.rsplit(":", 1)[-1])
            assert e18_adapter_rows[case_id]["outcome"][0] in {"abstain", "covered"}, case_id
            assert e18_adapter_rows[case_id]["outcome"][0] != "candidate", case_id


def test_e17_adapter_oracle_carries_the_clearance_and_nothing_else(
    e17_adapter_rows: dict[str, dict[str, Any]],
) -> None:
    """E17 N1 becomes a positive clearance; the two 3.4 candidates and nine negatives hold."""

    movements: set[str] = set()
    for row in _envelope_cases("E17"):
        case_id = str(row.key.rsplit(":", 1)[-1])
        expected = _MOVERS.get(case_id, [row.baseline.state, row.baseline.reason_or_classification])
        actual = e17_adapter_rows[case_id]
        assert actual["outcome"] == expected, case_id
        assert actual["finding_count"] == 0, case_id
        if actual["outcome"] != [row.baseline.state, row.baseline.reason_or_classification]:
            movements.add(case_id)
    assert movements == {"e2d8b1bdf4baa671a1b4"}
    n1 = e17_adapter_rows["e2d8b1bdf4baa671a1b4"]
    assert n1["outcome"] == ["covered", "complete"]
    assert n1["authorized_count"] == 4
    assert n1["corrected_positions"] == [0, 1, 2, 3]
    assert n1["candidate_records"] == 0
    for row in _envelope_cases("E17"):
        if row.role.startswith("N"):
            case_id = str(row.key.rsplit(":", 1)[-1])
            assert e17_adapter_rows[case_id]["outcome"][0] != "candidate", case_id


def test_all_185_source_rows_match_the_pinned_oracle(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    assert len(executed_case_rows) == 185
    for key, row in executed_case_rows.items():
        expected = _EXPECTED_ROWS[key]
        assert row["json"] == expected["expected_source_analyzer_row"], key
        assert row["census"] == expected["expected_admission_census"], key


def test_the_movement_set_is_exactly_the_four_pinned_rows(
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
        {"authorized_count": 5, "corrected_positions": []},
    ]
    assert executed_case_rows[_MOVEMENT_KEYS[1]]["json"] == [
        "covered",
        "complete",
        {"authorized_count": 4, "corrected_positions": [0, 1, 2, 3]},
    ]
    assert executed_case_rows[_MOVEMENT_KEYS[2]]["json"] == [
        "candidate",
        "none",
        {"authorized_count": 6, "corrected_positions": []},
    ]
    assert executed_case_rows[_MOVEMENT_KEYS[3]]["json"] == [
        "candidate",
        "none",
        {"authorized_count": 5, "corrected_positions": []},
    ]
    lost = [
        key
        for key, row in executed_case_rows.items()
        if row["case"].baseline.state in {"candidate", "covered"}
        and row["outcome"] != row["case"].baseline
    ]
    assert lost == []


def test_all_120_e10_to_e17_rows_and_all_50_corpus_rows_are_byte_identical(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    moved = [
        key
        for key, row in executed_case_rows.items()
        if row["case"].envelope != "E18"
        and key not in _ADAPTER_SHORT_CIRCUIT
        and row["outcome"] != row["case"].baseline
    ]
    assert moved == [
        "E15:P3:afe47b2a7ea87ed21a69",
        "E17:N1:e2d8b1bdf4baa671a1b4",
    ]
    assert (
        sum(row["case"].envelope not in {None, "E18"} for row in executed_case_rows.values()) == 120
    )
    assert sum(row["case"].envelope is None for row in executed_case_rows.values()) == 50
    assert sum(row["case"].envelope == "E18" for row in executed_case_rows.values()) == 15


@pytest.mark.parametrize("key", sorted(_ADAPTER_SHORT_CIRCUIT))
def test_no_production_crosses_an_adapter_short_circuit(
    key: str, executed_case_rows: dict[str, dict[str, Any]]
) -> None:
    """E10 N7 and corpus spec-30 resolve at adapter level before the source analyzer."""

    row = executed_case_rows[key]
    expected = _EXPECTED_ROWS[key]
    assert expected["adapter_short_circuit"] is True
    assert row["json"] == expected["expected_source_analyzer_row"]
    assert row["census"] == dict.fromkeys(ADMISSION_KINDS, 0)


def test_none_flip_populations_and_retro_recall_are_exact(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    opened = [row for row in executed_case_rows.values() if row["case"].envelope is not None]
    corpus = [row for row in executed_case_rows.values() if row["case"].envelope is None]
    opened_negatives = [row for row in opened if row["case"].designed_class == "negative"]
    corpus_correct = [row for row in corpus if row["case"].designed_class == "correct"]
    corpus_misstep = [row for row in corpus if row["case"].designed_class == "misstep"]
    assert len(opened_negatives) == 81
    assert len(corpus_correct) == 25
    assert len(corpus_misstep) == 25
    assert sum(row["json"][0] == "candidate" for row in opened_negatives) == 0
    assert sum(row["json"][0] == "candidate" for row in corpus_correct) == 0
    assert sum(row["json"][0] == "candidate" for row in corpus_misstep) == 19

    retro = {}
    for envelope in ("E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18"):
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
        "E15": "4/6",
        "E16": "4/6",
        "E17": "6/6",
        "E18": "4/6",
    }
    assert retro == _EXPECTED["totals"]["retro_recall"]
    assert sum(int(value.split("/")[0]) for value in retro.values()) == 43


def test_admission_census_over_the_185_evidence_rows_is_exact(
    executed_case_rows: dict[str, dict[str, Any]],
) -> None:
    rows = {
        kind: sorted(key for key, row in executed_case_rows.items() if row["census"][kind])
        for kind in ADMISSION_KINDS
    }
    assert rows == {
        "d1-format-arm": ["E18:P2:5a9277448db34379ce78"],
        "d2-set-selector": [],
        "d3-csv-reader": [],
        "d4a-numeric-group": [
            "E17:N1:e2d8b1bdf4baa671a1b4",
            "E18:P3:d1b1fc47ccdabd0c2f22",
        ],
        "d4b-loop-terminal": [
            "E17:N1:e2d8b1bdf4baa671a1b4",
            "E18:P3:d1b1fc47ccdabd0c2f22",
        ],
        "d5-cardinality-read": [
            "E15:P3:afe47b2a7ea87ed21a69",
            "E17:N1:e2d8b1bdf4baa671a1b4",
        ],
    }
    assert rows == _EXPECTED["totals"]["evidence_admission_rows"]
    totals = {
        kind: sum(row["census"][kind] for row in executed_case_rows.values())
        for kind in ADMISSION_KINDS
    }
    assert totals == {
        "d1-format-arm": 2,
        "d2-set-selector": 0,
        "d3-csv-reader": 0,
        "d4a-numeric-group": 4,
        "d4b-loop-terminal": 2,
        "d5-cardinality-read": 2,
    }
    # Across 185 evidence cases the shipped productions fire on exactly four rows, and every one
    # of them is a pinned movement.
    fired = {key for kind in ADMISSION_KINDS for key in rows[kind]}
    assert fired == set(_MOVEMENT_KEYS)


def test_the_question_census_stays_at_28_with_an_empty_removed_set(
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
    } == {"opened": 19, "corpus": 9, "total": 28}
    assert sorted(before - after) == []
    assert _EXPECTED["totals"]["question_census"]["removed"] == []


def test_sealed_envelope_18_bytes_and_scoring_are_untouched() -> None:
    """The three retro catches are development evidence; sealed E18 stays 2/6."""

    audit = json.loads((_E18 / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    role_map = json.loads((_E18 / "ROLE_MAP.json").read_text(encoding="utf-8"))
    assert len(role_map["case_roles_in_fixed_order"]) == 15
    assert audit["first_contact_recall"].startswith("2/6")
    e17 = json.loads((_E17 / "AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    assert e17["first_contact_recall"].startswith("4/6")
    e15 = json.loads(
        (
            Path("evaluation/development/blind-envelope-15-2026-08-29") / "AUDIT_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    assert e15["first_contact_recall"].startswith("2/6")
