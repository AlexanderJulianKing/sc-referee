from __future__ import annotations

import ast
import hashlib
import inspect
import json
import runpy
import sys
import types
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_3 import (
    _CLOSED_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v32,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v33,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_helper_record_v3_3 import (
    build_helper_record_graph,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
    _control_identity,
    prove_terminal_presentation,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_3/prototype-sweep").resolve()
_PINNED = {
    "instrument_results.json": "03c7aa815b8728bf9452afe666f9738e9501f345903ce7ef7fe3f520c320134f",
    "results.json": "be9ddd1ea4b8bd27faff92392865cbb76f14fbf6b162f847523fe5900d1bd7ad",
    "MANIFEST.json": "10e94f5a056e50662bfc65bfafc2ebec0ea519a4c7bef1f5269caddf6523bf5f",
}

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
    _catalog = runpy.run_path(str(_ROOT / "fixture_catalog.py"))
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_FIXTURES = tuple(_catalog["all_fixtures"]())
_RESULT_ROWS = {
    row["name"]: row["outcome"]
    for row in json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))["fixtures"]
}
_REFERENCE_CASE = cast(Callable[[str], Any], _harness["reference_case"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _harness["classify"])


def _run(fixture: Any, analyzer: Callable[..., MultipleTestingDataflowResult]) -> Any:
    values = _INPUTS(_REFERENCE_CASE(fixture.case_key), fixture.source)
    content = cast(bytes, values.pop("content"))
    return _CLASSIFY(analyzer(content, **values))


def _outcome_tuple(value: Any) -> tuple[str, str, tuple[int, ...], int | None]:
    return (
        value.state,
        value.reason_or_classification,
        tuple(value.corrected_positions),
        value.authorized_count,
    )


def _json_outcome_tuple(value: list[object]) -> tuple[str, str, tuple[int, ...], int | None]:
    if len(value) == 2:
        return str(value[0]), str(value[1]), (), None
    detail = cast(dict[str, object], value[2])
    positions = cast(list[int], detail["corrected_positions"])
    count = detail.get("authorized_count")
    return str(value[0]), str(value[1]), tuple(positions), cast(int | None, count)


def test_pinned_prototype_evidence_is_immutable() -> None:
    assert {
        name: hashlib.sha256((_ROOT / name).read_bytes()).hexdigest() for name in _PINNED
    } == _PINNED


@pytest.mark.parametrize("fixture", _FIXTURES, ids=lambda item: item.name)
def test_all_203_fixture_rows_execute(fixture: Any) -> None:
    assert _outcome_tuple(_run(fixture, analyze_v33)) == _json_outcome_tuple(
        _RESULT_ROWS[fixture.name]
    )


_NEW_ADVERSARIES = tuple(
    item for item in _FIXTURES if item.category in {"terminal-adversary", "helper-adversary"}
)


@pytest.mark.parametrize("fixture", _NEW_ADVERSARIES, ids=lambda item: item.name)
def test_new_adversary_matrix(fixture: Any) -> None:
    result = _run(fixture, analyze_v33)
    assert result.state == "abstain"
    assert result.reason_or_classification == fixture.expected.reason_or_classification


_POSITIVES = tuple(
    item for item in _FIXTURES if item.category in {"terminal-positive", "helper-positive"}
)


@pytest.mark.parametrize("fixture", _POSITIVES, ids=lambda item: item.name)
def test_positive_controls_classify_once_without_a_finding(fixture: Any) -> None:
    result = _run(fixture, analyze_v33)
    assert _outcome_tuple(result) == _outcome_tuple(fixture.expected)
    assert result.state == "candidate"
    assert result.reason_or_classification == "none"


_HIERARCHY = tuple(item for item in _FIXTURES if item.category == "frozen-gatekeeping")


@pytest.mark.parametrize("fixture", _HIERARCHY, ids=lambda item: item.name)
def test_frozen_hierarchy_rows_match_both_lanes(fixture: Any) -> None:
    assert _outcome_tuple(_run(fixture, analyze_v32)) == _outcome_tuple(fixture.expected)
    assert _outcome_tuple(_run(fixture, analyze_v33)) == _outcome_tuple(fixture.expected)


def test_fixture_census_and_none_flip_populations_are_exact() -> None:
    assert len(_FIXTURES) == 203
    counts = Counter(item.category for item in _FIXTURES)
    assert counts == {
        "frozen-v3-original": 48,
        "audit-fix-r1": 14,
        "audit-fix-r2": 4,
        "audit-fix-r3": 5,
        "b5-expression-variant": 63,
        "v3.1-laundering-adjacent": 16,
        "ap-v3.2": 20,
        "frozen-gatekeeping": 12,
        "terminal-positive": 3,
        "terminal-adversary": 10,
        "helper-positive": 1,
        "helper-adversary": 7,
    }
    assert sum(item.correct_analysis for item in _FIXTURES) == 183


def test_terminal_and_helper_proofs_are_idempotent_graph_facts() -> None:
    terminal = next(
        item for item in _POSITIVES if item.name == "positive-terminal-verdict-record-print"
    )
    first_terminal = prove_terminal_presentation(terminal.source)
    second_terminal = prove_terminal_presentation(terminal.source)
    assert first_terminal == second_terminal
    assert first_terminal is not None and len(first_terminal.positions) == 1

    helper = next(
        item
        for item in _POSITIVES
        if item.name == "positive-helper-record-single-call-comprehension"
    )
    outcome_columns = tuple(
        _INPUTS(_REFERENCE_CASE(helper.case_key), helper.source)["outcome_columns"]
    )
    first_helper = build_helper_record_graph(helper.source, outcome_columns)
    second_helper = build_helper_record_graph(helper.source, outcome_columns)
    assert first_helper is not None and second_helper is not None
    assert first_helper.detail == second_helper.detail
    assert ast.dump(first_helper.tree, include_attributes=True) == ast.dump(
        second_helper.tree, include_attributes=True
    )
    assert "__mt33" in ast.dump(first_helper.tree, include_attributes=False)


def test_terminal_occurrence_identity_includes_control_owner() -> None:
    left_test = ast.Name(id="p", ctx=ast.Load())
    right_test = ast.Name(id="p", ctx=ast.Load())
    left = ast.If(test=left_test, body=[ast.Pass()], orelse=[])
    right = ast.IfExp(test=right_test, body=ast.Constant("a"), orelse=ast.Constant("b"))
    for node in (left, left_test, right, right_test):
        node.lineno = 10
        node.col_offset = 4
        node.end_lineno = 10
        node.end_col_offset = 5
    assert _control_identity(left_test, left) != _control_identity(right_test, right)


def test_closed_reason_set_remains_exactly_frozen_61() -> None:
    from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_2 import (
        _CLOSED_REASONS as FROZEN_REASONS,
    )

    assert _CLOSED_REASONS == FROZEN_REASONS
    assert len(_CLOSED_REASONS) == 61


def test_frozen_v3_2_anchor_bytes_are_exact() -> None:
    root = Path(__file__).resolve().parents[1]
    pinned = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py": "38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_2.py": "919a82cd90391358aa6102db0870ba7af64190949b7bf057c261088611a4e32f",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py": "b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_2.py": "24945b3db1b9ee9a6d6b1e53983cbef0783a7395bd3c53287828fd2d3be0d91b",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v3_2.py": "f845dc1f03f7e337fb6ba00bef811a7d319f857cf5ee9643f28c524c846387ea",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_2.py": "3805178737607d4dbf1769286d2b10eb84f408efc566bc5a2af892d9c6bee5da",
        "src/sc_referee/scientific_checks/multiple_testing_scope_questions_v3_2.py": "fa183fc97a899109b7c000b0ad28f2d2020c443e591daa34cbbaed3172d7464e",
        "src/sc_referee/multiple_testing_scope_attestations_v3_2.py": "8f1ae9e4d02189d40bfe078e4dbf46e446af44433c876abc5b02081dc8ecfd9c",
        "docs/implementation/MULTITEST-3.2-CORRECTION-RECOGNITION-DESIGN-2026-08-29.md": "81e5db51d8f93983497baa7c121dc28ac7dbd3e959dc4961696b87f7e27641bf",
        "evaluation/development/multitest-code-slice-v3_2/prototype-sweep/results.json": "4a512d5e2cf007192430f3d0abacfd614535e2e23348245d4bc8ce8b9f07d80c",
        "evaluation/development/multitest-code-slice-v3_2/prototype-sweep/MANIFEST.json": "3a88349d481cd55378c42723cef3a022672ecfc119fcf723aac05f88d581888e",
        "evaluation/development/multitest-open-corpus-v1/adapter_replay_records_v2_1.json": "7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502",
    }
    assert {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in pinned
    } == pinned


def test_production_uses_graph_facts_without_source_rewrite_or_monkeypatch() -> None:
    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_3 as dataflow

    analyzer_source = inspect.getsource(dataflow.analyze_code_csv_multiple_testing_dataflow)
    module_source = Path(dataflow.__file__).read_text(encoding="utf-8")
    assert "ast.unparse" not in module_source
    assert "monkeypatch" not in module_source
    assert "setattr(_MtEngine" not in module_source
    assert "terminal_exclusions" in analyzer_source
    assert "analysis_tree" in analyzer_source
