"""Seven named mutation kills for the multiple-testing 3.5 recall deltas.

Each kill removes exactly one production, or loosens exactly one of its refusals, or breaks the
ordering rule, and then names the row that moves.  A kill that stops moving its row means the
gate it guards has stopped carrying weight, which is a stronger failure signal than a passing
outcome test.

Every mutant is applied, observed, and reverted inside one `monkeypatch` context, and each test
asserts the unmutated answer on both sides of the mutation so a leaked patch cannot pass.
"""

from __future__ import annotations

import ast
import runpy
import sys
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_core_v3_5 as core35
from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_5 as lane35
from sc_referee.scientific_checks import code_csv_multiple_testing_recall_deltas_v3_5 as deltas
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_5 import (
    admission_census,
    recording_admissions,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_5/prototype-sweep").resolve()

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_SWEEP / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
    _catalog = runpy.run_path(str(_SWEEP / "fixture_catalog.py"))
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_REFERENCE_CASE = cast(Callable[[str], Any], _harness["reference_case"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[Any], Any], _harness["classify"])
_ALL_FIXTURES = cast(Callable[[], tuple[Any, ...]], _catalog["all_fixtures"])


@contextmanager
def _harness_installed() -> Iterator[None]:
    """The chained 3.4 and 3.3 catalogs import `harness` at module level when they are run.

    `fixture_catalog.prior_fixtures()` executes those files at call time, not at import time, so
    the module has to be back on `sys.modules` for the duration of the call.
    """

    previous = sys.modules.get("harness")
    sys.modules["harness"] = _harness_module
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop("harness", None)
        else:
            sys.modules["harness"] = previous


_E15_P3 = "E15:P3:afe47b2a7ea87ed21a69"
_E18_P2 = "E18:P2:5a9277448db34379ce78"
_E18_P3 = "E18:P3:d1b1fc47ccdabd0c2f22"

_E15_P3_CANDIDATE: list[object] = [
    "candidate",
    "none",
    {"authorized_count": 5, "corrected_positions": []},
]
_E18_P2_CANDIDATE: list[object] = [
    "candidate",
    "none",
    {"authorized_count": 6, "corrected_positions": []},
]
_E18_P3_CANDIDATE: list[object] = [
    "candidate",
    "none",
    {"authorized_count": 5, "corrected_positions": []},
]


def _fixture(name: str) -> Any:
    with _harness_installed():
        matches = [item for item in _ALL_FIXTURES() if item.name == name]
    if len(matches) != 1:
        raise LookupError(f"fixture {name} is not unique")
    return matches[0]


def _arguments(case_key: str, source: bytes | None) -> tuple[bytes, dict[str, Any]]:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    return cast(bytes, values.pop("content")), values


def _row(case_key: str, source: bytes | None = None) -> tuple[list[object], dict[str, int]]:
    content, values = _arguments(case_key, source)
    with recording_admissions():
        result = lane35.analyze_code_csv_multiple_testing_dataflow(content, **values)
        census = admission_census()
    return cast(list[object], _CLASSIFY(result).as_json()), census


def _reanalysis_reason(case_key: str, source: bytes | None = None) -> str | None:
    content, values = _arguments(case_key, source)
    return lane35._reanalyze_with_v35_productions(content, **values).reason


# ======================================================================================
# D1
# ======================================================================================


def test_kill_a_dropping_d1_loses_the_e18_p2_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutant: the widened arm predicate admits nothing, leaving the frozen bare-constant rule.

    E18 P2's verdict conditional formats both of its arms with `str.format`, which is the whole
    reason the frozen hierarchy guard refused the row.  With D1 dropped the row must fall back
    to its frozen 3.4 reason byte-for-byte and lose its candidate.
    """

    assert _row(_E18_P2)[0] == _E18_P2_CANDIDATE
    with monkeypatch.context() as patch:
        patch.setattr(core35, "_v35_widened_display_arm", lambda node, constants: False)
        mutated, census = _row(_E18_P2)
        assert mutated == ["abstain", "hierarchical-gatekeeping-present"]
        assert census["d1-format-arm"] == 0
    assert _row(_E18_P2)[0] == _E18_P2_CANDIDATE


def test_kill_b_admitting_p_value_interpolation_flips_the_d1_refusal_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: `ARGVAL` also admits any loaded name, so a p-derived value can reach a display arm.

    `correct-d1-arm-interpolates-p-value` is a correct analysis whose verdict arm interpolates
    the p-value itself.  Interpolating a p-derived value would give the assigned verdict name a
    p-lineage it does not have, so the shipped grammar refuses it and the fixture's census stays
    empty.  Under the mutant the arm is admitted twice and the fixture's own disqualifier
    assertion -- `refused_admission: d1-format-arm` -- no longer holds.
    """

    fixture = _fixture("correct-d1-arm-interpolates-p-value")

    def loose(node: ast.expr, constants: frozenset[str]) -> bool:
        loaded = frozenset(
            item.id
            for item in ast.walk(node)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        )
        return deltas.widened_display_arm(node, constants | loaded)

    before, census = _row(fixture.case_key, fixture.source)
    assert before[0] == "abstain"
    assert census["d1-format-arm"] == 0
    with monkeypatch.context() as patch:
        patch.setattr(core35, "_v35_widened_display_arm", loose)
        _mutated, mutated_census = _row(fixture.case_key, fixture.source)
        assert mutated_census["d1-format-arm"] == 2
    after, after_census = _row(fixture.case_key, fixture.source)
    assert (after, after_census["d1-format-arm"]) == (before, 0)


# ======================================================================================
# D4
# ======================================================================================


def test_kill_c_dropping_d4b_puts_e18_p3_back_on_the_hierarchy_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the sixth `For` exemption never fires.

    This is the measurement that made 4a and 4b a pair.  With the loop exemption gone the 3.5
    re-analysis of E18 P3 abstains at `hierarchical-gatekeeping-present` rather than
    classifying, and the ordering rule then publishes the frozen 3.4 reason
    `test-operand-lineage-unresolved`.  D4a is still firing throughout, so this kill isolates
    D4b: 4a alone reaches only a different abstention, which is no public change at all.
    """

    assert _row(_E18_P3)[0] == _E18_P3_CANDIDATE
    assert _reanalysis_reason(_E18_P3) is None
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_v35_terminal_presentation_loop", lambda self, node: False)
        assert _reanalysis_reason(_E18_P3) == "hierarchical-gatekeeping-present"
        mutated, census = _row(_E18_P3)
        assert mutated == ["abstain", "test-operand-lineage-unresolved"]
        assert census["d4b-loop-terminal"] == 0
        assert census["d4a-numeric-group"] > 0
    assert _row(_E18_P3)[0] == _E18_P3_CANDIDATE


def test_kill_d_admitting_not_equal_flips_the_d4a_refusal_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the comparator grammar accepts `!=` as well as `==`.

    `correct-d4a-not-equal-operator` selects its group by elimination.  Admitting `!=` would
    require returning the *other* group token, which means reading the binary group domain
    inside a predicate that does not hold it, so the grammar refuses the operator outright.
    The kill is asserted where D4a actually decides, on the production predicate over the
    fixture's own bytes: shipped it admits no comparator, mutated it admits both and maps them
    to real CSV group tokens.

    Recorded, because it is the honest reading of this kill: the engine's own frozen `Eq`
    requirement in `_bare_group_mask_frame` and `_mask_rows` independently refuses a `!=` mask,
    so the fixture's published row does not move even under the mutant.  That is defence in
    depth, not a missing kill, and the second half of this test pins it.
    """

    fixture = _fixture("correct-d4a-not-equal-operator")
    values = _INPUTS(_REFERENCE_CASE(fixture.case_key), fixture.source)
    arguments = {
        "group_column": values["group_column"],
        "group_values": tuple(values["group_values"]),
        "column_is_decimal": deltas.group_column_is_decimal(
            values["csv_content"], values["group_column"]
        ),
    }
    assert arguments["column_is_decimal"] is True
    tree = ast.parse(fixture.source)
    assert deltas.group_mask_numeric_positions(tree, **arguments) == {}

    swapped = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.NotEq)
    ]
    assert len(swapped) == 2
    for node in swapped:
        node.ops = [ast.Eq()]
    try:
        admitted = deltas.group_mask_numeric_positions(tree, **arguments)
    finally:
        for node in swapped:
            node.ops = [ast.NotEq()]
    assert sorted(admitted.values()) == sorted(values["group_values"])
    assert deltas.group_mask_numeric_positions(tree, **arguments) == {}

    # The engine refuses a `!=` mask on its own, so the census stays empty either way.
    _outcome, census = _row(fixture.case_key, fixture.source)
    assert census["d4a-numeric-group"] == 0
    with monkeypatch.context() as patch:
        patch.setattr(deltas, "group_mask_numeric_positions", lambda tree, **kw: admitted)
        patch.setattr(core35, "_v35_group_mask_numeric_positions", lambda tree, **kw: admitted)
        _mutated, mutated_census = _row(fixture.case_key, fixture.source)
        assert mutated_census["d4a-numeric-group"] == 0


# ======================================================================================
# D5
# ======================================================================================


def test_kill_e_dropping_d5_loses_the_e15_p3_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutant: the guard's sixth admitted `Call` form never fires.

    E15 P3's only wall is a `len()` over the reconstructed p-record family inside a display
    f-string, which the frozen off-grammar guard counted as an unaccounted-for p transform.
    Removing the admission puts the row back on `unresolved-manual-correction-present`.
    """

    assert _row(_E15_P3)[0] == _E15_P3_CANDIDATE
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_v35_cardinality_reads", lambda self: set())
        mutated, census = _row(_E15_P3)
        assert mutated == ["abstain", "unresolved-manual-correction-present"]
        assert census["d5-cardinality-read"] == 0
    assert _row(_E15_P3)[0] == _E15_P3_CANDIDATE


def test_kill_f_dropping_the_display_ancestor_chain_flips_the_d5_refusal_fixtures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: conditions 1 to 4 are kept and the display-ancestor chain of condition 5 is dropped.

    `correct-d5-len-bound-to-a-local-first` is the load-bearing disqualifier in delta 5, and this
    kill shows exactly why.  It stores the cardinality in a local before printing it, and a
    stored value is no longer provably display-only, so the shipped chain refuses the read and
    the row keeps its frozen 3.4 reason.  With the chain dropped the read is admitted and the
    row is published as a `candidate`: an admission the design never proved now decides a public
    row.  The chain is the only thing standing between the shipped lane and that.

    `correct-d5-len-in-a-comparison` is carried alongside as the census half of the same kill,
    where the value gates a branch rather than reaching a sink.
    """

    def loose(engine: Any) -> set[int]:
        expected = tuple(range(len(engine.outcome_columns)))
        shadowed = getattr(engine.resolver, "builtins_shadowed", frozenset())
        admitted: set[int] = set()
        for node in core35._walk_statements(engine.scope):
            if not (
                isinstance(node, ast.Call)
                and engine.resolver.qualified(node.func) == "len"
                and "len" not in shadowed
                and len(node.args) == 1
                and not node.keywords
                and isinstance(node.args[0], ast.Name)
            ):
                continue
            sequence = engine._p_sequence(node.args[0])
            if sequence is None or tuple(sequence) != expected:
                continue
            admitted.add(id(node))
        return admitted

    accusable = _fixture("correct-d5-len-bound-to-a-local-first")
    comparison = _fixture("correct-d5-len-in-a-comparison")
    assert accusable.refused_admission == "d5-cardinality-read"
    before, census = _row(accusable.case_key, accusable.source)
    assert before == ["abstain", "unresolved-manual-correction-present"]
    assert census["d5-cardinality-read"] == 0
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_v35_cardinality_reads", loose)
        mutated, mutated_census = _row(accusable.case_key, accusable.source)
        assert mutated == [
            "candidate",
            "none",
            {"authorized_count": 5, "corrected_positions": []},
        ]
        assert mutated_census["d5-cardinality-read"] == 1
        _row_two, comparison_census = _row(comparison.case_key, comparison.source)
        assert comparison_census["d5-cardinality-read"] == 1
    after, after_census = _row(accusable.case_key, accusable.source)
    assert (after, after_census["d5-cardinality-read"]) == (before, 0)
    assert _row(comparison.case_key, comparison.source)[1]["d5-cardinality-read"] == 0


# ======================================================================================
# the ordering rule
# ======================================================================================


def test_kill_g_breaking_the_ordering_rule_moves_two_named_rows_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: an abstaining 3.5 re-analysis returns its own reason, not the frozen 3.4 one.

    Two named rows move, and the first of them is the serious one.
    `correct-helper-record-unresolved-consumer` is a **frozen 3.4 fixture**: its published
    reason is `unresolved-pvalue-consumer` and it must stay that way forever.  The 3.5
    re-analysis, which runs the 3.4 comprehension normalization over the widened engine,
    abstains at `pderived-conclusion-family-incomplete` instead, so publishing the re-analysis
    reason moves a frozen row.  That is design stop rule 3.

    `correct-d4b-loop-early-return` is the second: a 3.5 fixture whose frozen reason is
    `test-operand-lineage-unresolved` and whose re-analysis reason is
    `hierarchical-gatekeeping-present`.
    """

    original = lane35.analyze_code_csv_multiple_testing_dataflow

    def broken(content: bytes, **arguments: Any) -> Any:
        frozen = lane35._frozen_v34_analyze(content, **arguments)
        if frozen.reason is None:
            return frozen
        return lane35._reanalyze_with_v35_productions(content, **arguments)

    expected = {
        "correct-helper-record-unresolved-consumer": (
            ["abstain", "unresolved-pvalue-consumer"],
            ["abstain", "pderived-conclusion-family-incomplete"],
        ),
        "correct-d4b-loop-early-return": (
            ["abstain", "test-operand-lineage-unresolved"],
            ["abstain", "hierarchical-gatekeeping-present"],
        ),
    }
    for name, (frozen_row, mutated_row) in expected.items():
        fixture = _fixture(name)
        assert _row(fixture.case_key, fixture.source)[0] == frozen_row, name
        with monkeypatch.context() as patch:
            patch.setattr(lane35, "analyze_code_csv_multiple_testing_dataflow", broken)
            assert _row(fixture.case_key, fixture.source)[0] == mutated_row, name
        assert _row(fixture.case_key, fixture.source)[0] == frozen_row, name
    assert lane35.analyze_code_csv_multiple_testing_dataflow is original
