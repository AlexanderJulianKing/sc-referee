"""MT 3.5 audit-fix round 3: lexical scope, match captures and record positions.

The eighteen-row oracle is independent of analyzer output, reproduces all eight source digests
published by the round-2 audit, and executes through both the analyzer and real adapter pipeline.
Four mutation kills separately demonstrate the scope, match, unknown-position and indexed-record
rules.  No new reason is introduced; refusals use the existing consumption reason.
"""

from __future__ import annotations

import ast
import hashlib
import json
import runpy
import shutil
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_core_v3_5 as core35
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_5 import (
    CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
    admission_census,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v34,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_5 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v35,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_5/prototype-sweep").resolve()
_ORACLE = Path("evaluation/development/multitest-code-slice-v3_5/audit-fix-r3-oracle").resolve()
_SEALED_CASE = Path(
    "evaluation/development/blind-envelope-18-2026-09-01/cases/5c091f9052becdb5c3ea"
).resolve()

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_SWEEP / "harness.py"))
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_REFERENCE_CASE = cast("Callable[[str], Any]", _harness["reference_case"])
_INPUTS = cast("Callable[[Any, bytes | None], dict[str, Any]]", _harness["inputs"])
_CLASSIFY = cast("Callable[[Any], Any]", _harness["classify"])
_ADAPTER = cast(
    "Callable[[Path, bytes], dict[str, Any]]",
    runpy.run_path("evaluation/development/multitest-recall-recon-e13/h.py")["adapter_envelope"],
)

_MODULE = runpy.run_path(str(_ORACLE / "fixture_sources.py"))
_SOURCES = cast("dict[str, tuple[str, bytes]]", _MODULE["fixture_sources"]())
_CODEX_DIGESTS = cast("dict[str, str]", _MODULE["CODEX_DIGESTS"])
_EXPECTED = json.loads((_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_ROWS = cast("list[dict[str, Any]]", _EXPECTED["rows"])
_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _ROWS}

_CONSUMPTION_REASON = "unresolved-manual-correction-present"
_CLEARED = ("covered", "complete", (0, 1, 2, 3, 4), 5)
_REFUSED = ("abstain", _CONSUMPTION_REASON, (), None)


def _outcome_tuple(value: Any) -> tuple[str, str, tuple[int, ...], int | None]:
    return (
        value.state,
        value.reason_or_classification,
        tuple(value.corrected_positions),
        value.authorized_count,
    )


def _expected_tuple(row: dict[str, Any]) -> tuple[str, str, tuple[int, ...], int | None]:
    return (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row["expected_corrected_positions"])),
        cast("int | None", row["expected_authorized_count"]),
    )


def _pipeline_tuple(value: dict[str, Any]) -> tuple[str, str, tuple[int, ...], int | None]:
    corrected = cast("list[int] | None", value.get("corrected_positions"))
    return (
        str(value["outcome"][0]),
        str(value["outcome"][1]),
        tuple(corrected or ()),
        cast("int | None", value.get("authorized_count")),
    )


def _run_v35(case_key: str, source: bytes) -> tuple[Any, dict[str, int]]:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    with recording_admissions():
        result = analyze_v35(content, **values)
        census = admission_census()
    return _CLASSIFY(result), {kind: count for kind, count in census.items() if count}


def _run_v34(case_key: str, source: bytes) -> Any:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    return _CLASSIFY(analyze_v34(content, **values))


def _row(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _SOURCES[name]
    outcome, _census = _run_v35(case_key, source)
    return _outcome_tuple(outcome)


@pytest.fixture(scope="session")
def audit_fix_r3_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _SOURCES.items():
        outcome, census = _run_v35(case_key, source)
        rows[name] = {
            "outcome": outcome,
            "census": census,
            "frozen": _run_v34(case_key, source),
        }
    return rows


@pytest.fixture(scope="session")
def audit_fix_r3_pipeline_rows(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    staging = tmp_path_factory.mktemp("mt35-r3-adapter")
    rows: dict[str, Any] = {}
    for name, (_case_key, source) in _SOURCES.items():
        case = staging / name
        case.mkdir()
        shutil.copytree(_SEALED_CASE / "project", case / "project")
        shutil.copy2(_SEALED_CASE / "profile_1_2_0.json", case / "profile_1_2_0.json")
        (case / "PROMPT.txt").write_text("Static scientific audit.\n", encoding="utf-8")
        rows[name] = _ADAPTER(case, source)
    return rows


def test_round_3_oracle_is_independent_and_source_complete() -> None:
    assert _EXPECTED["provenance"]["implementation_output_used"] is False
    assert len(_ROWS) == 18
    assert set(_ROWS_BY_NAME) == set(_SOURCES)
    assert hashlib.sha256(cast(Path, _MODULE["E18_N1"]).read_bytes()).hexdigest() == str(
        _MODULE["E18_N1_SHA256"]
    )
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _SOURCES.items()
    } == {name: str(row["fixture_source_sha256"]) for name, row in _ROWS_BY_NAME.items()}
    for _name, (_case_key, source) in _SOURCES.items():
        ast.parse(source)


def test_the_eight_audit_sources_are_the_verdicts_own_bytes() -> None:
    assert len(_CODEX_DIGESTS) == 8
    for name, digest in _CODEX_DIGESTS.items():
        assert hashlib.sha256(_SOURCES[name][1]).hexdigest() == digest, name


@pytest.mark.parametrize("row", _ROWS, ids=lambda row: row["fixture_name"])
def test_all_18_round_3_rows_execute(
    row: dict[str, Any], audit_fix_r3_rows: dict[str, dict[str, Any]]
) -> None:
    name = str(row["fixture_name"])
    observed = audit_fix_r3_rows[name]
    assert _outcome_tuple(observed["outcome"]) == _expected_tuple(row)
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v34_identical"])


@pytest.mark.parametrize("row", _ROWS, ids=lambda row: row["fixture_name"])
def test_all_18_round_3_rows_execute_through_the_real_pipeline(
    row: dict[str, Any], audit_fix_r3_pipeline_rows: dict[str, Any]
) -> None:
    name = str(row["fixture_name"])
    assert _pipeline_tuple(audit_fix_r3_pipeline_rows[name]) == _expected_tuple(row)


def test_no_correct_round_3_control_is_accused(
    audit_fix_r3_rows: dict[str, dict[str, Any]],
) -> None:
    correct = [str(row["fixture_name"]) for row in _ROWS if row["correct_analysis"]]
    assert len(correct) == 13
    assert {
        name for name in correct if audit_fix_r3_rows[name]["outcome"].state == "candidate"
    } == set()


def test_the_closed_reason_set_is_unchanged_by_round_3() -> None:
    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61
    assert core35._MT35_CONSUMPTION_REASON == _CONSUMPTION_REASON
    for row in _ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS


def test_binding_sites_record_scope_and_every_match_capture_form() -> None:
    tree = ast.parse(
        """
def main():
    reject = correction()
    def nested(reject):
        reject = 1
        def reject():
            pass
        return lambda reject: reject
    class Reader:
        reject = None
        def method(self, reject):
            return reject
    copied = [reject for reject in values]
    match value:
        case [sequence, *star]:
            pass
        case {"key": mapping, **rest}:
            pass
        case Reader(positional, named=keyword):
            pass
        case ("x" as either) | ("y" as either):
            pass
        case _ as whole:
            pass
"""
    )
    sites = core35._mt35_binding_sites(tree)
    expected_captures = {
        "sequence",
        "star",
        "mapping",
        "rest",
        "positional",
        "keyword",
        "either",
        "whole",
    }
    assert expected_captures <= set(sites)
    assert all(
        any(site.kind == "match_capture" for site in sites[name]) for name in expected_captures
    )
    reject_scopes = {site.scope for site in sites["reject"]}
    assert len(reject_scopes) == 6
    correction_scope = next(
        site.scope
        for site in sites["reject"]
        if isinstance(site.value, ast.Call)
        and isinstance(site.value.func, ast.Name)
        and site.value.func.id == "correction"
    )
    for_target_scope = next(site.scope for site in sites["copied"] if site.kind == "assign")
    assert correction_scope == for_target_scope


# --- four named mutation kills ---------------------------------------------------------------


def test_kill_a_dropping_scope_awareness_accuses_the_three_blocker_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    names = (
        "codex-r3-scope-unused-nested-parameter-unrolled",
        "codex-r3-scope-unused-nested-local-unrolled",
        "codex-r3-scope-unused-class-attribute-unrolled",
    )
    for name in names:
        assert _row(name) == _CLEARED
    real = core35._mt35_binding_sites

    def flattened(tree: ast.Module) -> dict[str, list[core35._Mt35BindingSite]]:
        sites = real(tree)
        correction_scope = next(
            site.scope
            for entries in sites.values()
            for site in entries
            if isinstance(site.value, ast.Call)
            and core35._mt_callee_terminal(site.value.func) == "multipletests"
        )
        return {
            name: [replace(site, scope=correction_scope) for site in entries]
            for name, entries in sites.items()
        }

    with monkeypatch.context() as patch:
        patch.setattr(core35, "_mt35_binding_sites", flattened)
        for name in names:
            assert _row(name) == ("candidate", "none", (), 5), name
    for name in names:
        assert _row(name) == _CLEARED


def test_kill_b_dropping_match_binders_readmits_the_capture_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "codex-r3-match-capture-rebinds-reject"
    assert _row(name) == _REFUSED
    real = core35._mt35_binding_sites

    def without_match(tree: ast.Module) -> dict[str, list[core35._Mt35BindingSite]]:
        return {
            bound_name: [site for site in entries if site.kind != "match_capture"]
            for bound_name, entries in real(tree).items()
        }

    with monkeypatch.context() as patch:
        patch.setattr(core35, "_mt35_binding_sites", without_match)
        assert _row(name) == _CLEARED
    assert _row(name) == _REFUSED


def test_kill_c_restoring_the_all_positions_fallback_readmits_the_swapped_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "codex-r3-unrolled-results-swapped-decisions"
    assert _row(name) == _REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            core35._MtEngine,
            "_mt35_positioned_origins",
            lambda self, payload, decided: decided,
        )
        assert _row(name) == _CLEARED
    assert _row(name) == _REFUSED


def test_kill_d_dropping_results_subscript_resolution_costs_the_aligned_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "control-aligned-hand-unrolled-results"
    assert _row(name) == _CLEARED
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_mt35_record_position", lambda self, node: None)
        assert _row(name) == _REFUSED
    assert _row(name) == _CLEARED
