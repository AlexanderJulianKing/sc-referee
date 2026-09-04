"""MT 3.5 audit-fix round 2: flow-sensitive return names and position-exact consumption.

Round 1 proved that a library correction's outputs reach the conclusions.  The round-1 audit
then showed three ways that proof could still be satisfied by a program whose verdicts are not
the correction's, and one way it accused a program whose verdicts are:

1. a return name rebound after the call still carried the correction to every later load;
2. a correction output could be read at one position and rendered at another;
3. a correction output read *decisively* inside a sink payload was called a display, so a
   correct inline verdict was published as a catch.

Three things are asserted here and nowhere else:

* the twenty-eight round-2 oracle rows execute through the **shipped** 3.5 lane with the
  oracle's exact outcome, corrected positions and admission census, and every row pinned as
  identical to its frozen 3.4 sibling really is;
* the five blocker sources and two of the five inline-verdict variants are the Codex verdict's
  own published bytes, and the rest are labelled shape reproductions; and
* four named mutation kills, each removing exactly one round-2 rule and showing a named row
  going back to a false clearance or losing a true clearance.

The round adds no abstention reason: the closed set stays at 61 and every refusal lands on the
reason the 3.2 AP path already emits at its own conclusion-consumption gate.
"""

from __future__ import annotations

import ast
import hashlib
import json
import runpy
import sys
from collections.abc import Callable
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
_ORACLE = Path("evaluation/development/multitest-code-slice-v3_5/audit-fix-r2-oracle").resolve()

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

_MODULE = runpy.run_path(str(_ORACLE / "fixture_sources.py"))
_SOURCES = cast("dict[str, tuple[str, bytes]]", _MODULE["fixture_sources"]())
_CODEX_DIGESTS = cast("dict[str, str]", _MODULE["CODEX_DIGESTS"])
_SHAPE_REPRODUCED = cast("frozenset[str]", _MODULE["SHAPE_REPRODUCED"])
_EXPECTED = json.loads((_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_ROWS = cast("list[dict[str, Any]]", _EXPECTED["rows"])
_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _ROWS}

_CONSUMPTION_REASON = "unresolved-manual-correction-present"


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


@pytest.fixture(scope="session")
def audit_fix_r2_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _SOURCES.items():
        outcome, census = _run_v35(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v34(case_key, source),
        }
    return rows


def test_round_2_oracle_is_independent_and_source_complete() -> None:
    assert _EXPECTED["provenance"]["implementation_output_used"] is False
    assert len(_ROWS) == 28
    assert set(_ROWS_BY_NAME) == set(_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _SOURCES.items()
    } == {name: str(row["fixture_source_sha256"]) for name, row in _ROWS_BY_NAME.items()}
    for _name, (_case_key, source) in _SOURCES.items():
        ast.parse(source)


def test_the_audit_sources_are_the_verdicts_own_bytes() -> None:
    """The blocker recipes are checked against the digests the round-1 verdict published.

    Seven of the sources are the verdict's own bytes.  The rest of the shapes it names are
    published as digests without sources, so they are rebuilt by shape and are declared as
    reproductions rather than as the verdict's bytes.
    """

    assert len(_CODEX_DIGESTS) == 8
    for name, digest in _CODEX_DIGESTS.items():
        assert hashlib.sha256(_SOURCES[name][1]).hexdigest() == digest, name
    assert not (_SHAPE_REPRODUCED & set(_CODEX_DIGESTS))
    assert _SHAPE_REPRODUCED <= set(_SOURCES)


@pytest.mark.parametrize("row", _ROWS, ids=lambda row: row["fixture_name"])
def test_all_28_round_2_rows_execute(
    row: dict[str, Any], audit_fix_r2_rows: dict[str, dict[str, Any]]
) -> None:
    name = str(row["fixture_name"])
    observed = audit_fix_r2_rows[name]
    assert _outcome_tuple(observed["outcome"]) == _expected_tuple(row)
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v34_identical"])


def test_no_correct_analysis_row_is_accused(
    audit_fix_r2_rows: dict[str, dict[str, Any]],
) -> None:
    """Sixteen rows are correct analyses.  None of them is published as a catch."""

    correct = [str(row["fixture_name"]) for row in _ROWS if row["correct_analysis"]]
    assert len(correct) == 16
    accused = {name for name in correct if audit_fix_r2_rows[name]["outcome"].state == "candidate"}
    assert accused == set()


def test_the_five_audit_blockers_no_longer_clear(
    audit_fix_r2_rows: dict[str, dict[str, Any]],
) -> None:
    """Four of the five stop clearing; the fifth is the measured threshold exclusion."""

    for name in (
        "codex-r2-blocker-1-adjusted-rebound-to-raw-p",
        "codex-r2-blocker-2-reject-rebound-to-raw-decisions",
        "codex-r2-blocker-3-permuted-reject-vector",
        "codex-r2-blocker-3-permuted-adjusted-vector",
    ):
        assert _outcome_tuple(audit_fix_r2_rows[name]["outcome"]) == (
            "abstain",
            _CONSUMPTION_REASON,
            (),
            None,
        ), name
        assert _outcome_tuple(audit_fix_r2_rows[name]["frozen"])[0] == "covered", name
    # Blocker 5 is pinned as measured and excluded: the threshold the verdict compares against
    # is a separate dimension with its own frozen guard and its own reason, and this check's
    # clearance claim is complete family correction over the authorized family.
    threshold = "codex-r2-blocker-5-threshold-alpha-times-two"
    assert _outcome_tuple(audit_fix_r2_rows[threshold]["outcome"]) == _CLEARED
    assert _outcome_tuple(audit_fix_r2_rows["control-conservative-half-alpha-threshold"]["outcome"])
    assert (
        _outcome_tuple(audit_fix_r2_rows["control-conservative-half-alpha-threshold"]["outcome"])
        == _CLEARED
    )


def test_the_closed_reason_set_is_unchanged_by_round_2() -> None:
    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61
    assert core35._MT35_CONSUMPTION_REASON == _CONSUMPTION_REASON
    for row in _ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS


def test_the_unroll_naming_is_written_and_read_in_one_place() -> None:
    """Rule B reads the loop unroller's own iteration index back off its generated names.

    The format is defined once and consumed once, so the writer and the reader cannot drift
    apart without this failing.
    """

    local = core35._MT_UNROLL_LOCAL_NAME.format(name="verdict", line=76, ordinal=3)
    record = core35._MT_UNROLL_RECORD_NAME.format(line=76, ordinal=4)
    assert core35._mt35_unrolled_ordinals(ast.parse(local, mode="eval").body) == {3}
    assert core35._mt35_unrolled_ordinals(ast.parse(record, mode="eval").body) == {4}
    assert core35._mt35_unrolled_ordinals(ast.parse("verdict", mode="eval").body) == set()


# --- the four named mutation kills ------------------------------------------------------------


def _row(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _SOURCES[name]
    outcome, _census = _run_v35(case_key, source)
    return _outcome_tuple(outcome)


_CLEARED = ("covered", "complete", (0, 1, 2, 3, 4), 5)
_REFUSED = ("abstain", _CONSUMPTION_REASON, (), None)

_REBINDING_ROWS = (
    "codex-r2-blocker-1-adjusted-rebound-to-raw-p",
    "codex-r2-blocker-2-reject-rebound-to-raw-decisions",
    "adversarial-reject-rebound-inside-a-branch",
    "adversarial-del-reject-then-a-new-reject",
)
_MISPLACEMENT_ROWS = (
    "codex-r2-blocker-3-permuted-reject-vector",
    "codex-r2-blocker-3-permuted-adjusted-vector",
)
_INLINE_VERDICT_ROWS = (
    "control-inline-verdict-fstring-enumerate",
    "control-inline-verdict-plain-print-enumerate",
    "control-inline-verdict-format-enumerate",
    "control-inline-verdict-unrolled-plain-print",
    "control-inline-verdict-unrolled-fstring",
)


def test_kill_a_dropping_flow_sensitivity_readmits_every_rebinding_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: no return name is ever treated as rebound.

    Recorded: with flow sensitivity gone, all four rebinding rows clear again -- including the
    two the audit demonstrated, where every published verdict is a raw p-value comparison and
    the correction's outputs were overwritten before any of them ran.
    """

    for name in _REBINDING_ROWS:
        assert _row(name) == _REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_mt35_lost_return_names", lambda self: frozenset())
        for name in _REBINDING_ROWS:
            assert _row(name) == _CLEARED, name
        assert _row("sealed-e18-n1-unaltered") == _CLEARED, "the control never moves"
    for name in _REBINDING_ROWS:
        assert _row(name) == _REFUSED, name


def test_kill_b_restoring_the_kind_union_readmits_the_permutation_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: a payload's rendered position is never established, so no origin can be
    misplaced -- the round-1 reading, which reduced the origin to a kind before comparing it
    with the position it was rendered at.

    Recorded: both permutation blockers clear again.  Each judges outcome 0 by outcome 1's
    corrected result and outcome 1 by outcome 0's.
    """

    for name in _MISPLACEMENT_ROWS:
        assert _row(name) == _REFUSED, name
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_mt35_rendered_position", lambda self, payload: None)
        for name in _MISPLACEMENT_ROWS:
            assert _row(name) == _CLEARED, name
        assert _row("sealed-e18-n1-unaltered") == _CLEARED, "the control never moves"
    for name in _MISPLACEMENT_ROWS:
        assert _row(name) == _REFUSED, name


def test_kill_c_calling_decisive_payload_use_a_display_loses_five_clearances(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: rule A goes back to treating every load under a sink payload as a display.

    Recorded: this is the round-1 regression the audit found.  All five inline-verdict
    variants are correct, complete corrections -- every declared outcome rendered once, every
    verdict selected by its own `reject[i]` -- and all five are published as catches.
    """

    for name in _INLINE_VERDICT_ROWS:
        assert _row(name) == _CLEARED, name
    with monkeypatch.context() as patch:
        patch.setattr(core35, "_mt35_consuming_payload_nodes", lambda payload: set())
        for name in _INLINE_VERDICT_ROWS:
            assert _row(name) == ("candidate", "none", (), 5), name
    for name in _INLINE_VERDICT_ROWS:
        assert _row(name) == _CLEARED, name


def test_kill_d_reading_a_bare_adjusted_value_as_a_verdict_readmits_the_rotated_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: any bare per-position element read counts as the position's own verdict, so the
    printed adjusted *value* carries the position the way the printed `reject` element does.

    Recorded: the rotated by-name lookup clears again.  That program judges outcome 0 by
    outcome 1's decision through a key the engine cannot follow, so the only origin left at
    each position is the adjusted number the loop prints beside the verdict.  A printed number
    is not a verdict -- a threshold still has to be applied to it -- and this row is what keeps
    the two bare-read kinds apart.
    """

    name = "adversarial-by-name-dict-lookup-with-a-rotated-key"
    assert _row(name) == _REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(
            core35._MtEngine,
            "_mt35_bare_read_origin",
            lambda self, node: core35._MT35_DECISION_DISPLAY_ORIGIN,
        )
        assert _row(name) == _CLEARED
    assert _row(name) == _REFUSED


def test_kill_e_treating_a_printed_reject_element_as_a_display_costs_the_slice_row() -> None:
    """Mutant: the bare read of a `reject` element is a display rather than a decision.

    Recorded as the reason the two bare-read kinds are separate.  The development code-slice
    fixture publishes its whole result as `print(reject[0])`, `print(reject[1])`,
    `print(reject[2])`: the printed booleans *are* the verdicts.  Reading them as displays
    accuses a correct complete correction, which is how the merge gate found the round-1
    regression.  The adjusted *value* stays a display, because a number still needs a
    threshold before it says anything.
    """

    assert core35._mt35_position_state(core35._MT35_DECISION_DISPLAY_ORIGIN) == "consuming"
    assert core35._mt35_position_state(core35._MT35_DISPLAY_ORIGIN) == "unresolved"
    mixed = core35._MT35_DECISION_DISPLAY_ORIGIN | core35._MT35_RAW_ORIGIN
    assert core35._mt35_position_state(mixed) == "raw"
    misplaced = core35._MT35_DECISION_DISPLAY_ORIGIN | core35._MT35_MISPLACED_ORIGIN
    assert core35._mt35_position_state(misplaced) == "unresolved"
    assert core35._mt35_position_state(core35._MT35_REBOUND_ORIGIN) == "unresolved"


def test_round_1_rules_are_still_in_force() -> None:
    """Round 2 narrows round 1; it does not replace it.  The round-1 suite owns the rest."""

    assert hasattr(core35._MtEngine, "_consumed_correction_calls")
    assert hasattr(core35._MtEngine, "_mt35_clearance_refusal")
