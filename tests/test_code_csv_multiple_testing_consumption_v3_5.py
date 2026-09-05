"""MT 3.5 audit-fix round 1: the library-correction consumption proof.

Three things are asserted here and nowhere else:

1. the twenty-four round-1 oracle rows execute through the **shipped** 3.5 lane with the
   oracle's exact outcome, exact corrected positions and exact admission census, and every
   row pinned as identical to its frozen 3.4 sibling really is;
2. the twin equalities the oracle's expected rows are derived from -- a source with a dead
   correction statement carries the row its own twin without that statement carries -- are
   recomputed live rather than transcribed, so a wrong pin fails instead of passing; and
3. seven named mutation kills, each of which removes or widens exactly one rule and shows a
   named row moving back to a false clearance, losing a true accusation, or paying a cost a
   wider rule would charge.

The round adds no abstention reason: the closed set stays at 61 and the refusal lands on the
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
from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_5 as lane35
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
_ORACLE = Path("evaluation/development/multitest-code-slice-v3_5/audit-fix-r1-oracle").resolve()

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

_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_ORACLE / "fixture_sources.py"))["fixture_sources"](),
)
_EXPECTED = json.loads((_ORACLE / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_ROWS = cast("list[dict[str, Any]]", _EXPECTED["rows"])
_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _ROWS}

#: The reason the fix lands on.  It is the 3.2 AP path's conclusion-consumption reason, not a
#: new one, and this test is what keeps that true.
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
def audit_fix_r1_rows() -> dict[str, dict[str, Any]]:
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


def test_round_1_oracle_is_independent_and_source_complete() -> None:
    assert _EXPECTED["provenance"]["implementation_output_used"] is False
    assert len(_ROWS) == 24
    assert set(_ROWS_BY_NAME) == set(_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _SOURCES.items()
    } == {name: str(row["fixture_source_sha256"]) for name, row in _ROWS_BY_NAME.items()}
    # Every recipe is a syntactically valid program, so no row can pass on a parse failure.
    for _name, (_case_key, source) in _SOURCES.items():
        ast.parse(source)


def test_the_four_audit_reproducers_are_the_verdicts_own_bytes() -> None:
    """The recipes are checked against the digests the Codex 3.5 verdict published."""

    published = cast(
        "dict[str, str]", runpy.run_path(str(_ORACLE / "fixture_sources.py"))["CODEX_DIGESTS"]
    )
    assert len(published) == 4
    for name, digest in published.items():
        assert hashlib.sha256(_SOURCES[name][1]).hexdigest() == digest, name


@pytest.mark.parametrize("row", _ROWS, ids=lambda row: row["fixture_name"])
def test_all_24_round_1_rows_execute(
    row: dict[str, Any], audit_fix_r1_rows: dict[str, dict[str, Any]]
) -> None:
    name = str(row["fixture_name"])
    observed = audit_fix_r1_rows[name]
    assert _outcome_tuple(observed["outcome"]) == _expected_tuple(row)
    assert observed["census"] == row["expected_admission_census"]
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v34_identical"])


def test_no_correct_analysis_row_is_accused(
    audit_fix_r1_rows: dict[str, dict[str, Any]],
) -> None:
    """Ten rows are correct analyses.  None of them is published as a catch."""

    correct = [str(row["fixture_name"]) for row in _ROWS if row["correct_analysis"]]
    assert len(correct) == 10
    accused = {name for name in correct if audit_fix_r1_rows[name]["outcome"].state == "candidate"}
    assert accused == set()


@pytest.mark.parametrize(
    "name", [str(row["fixture_name"]) for row in _ROWS if row.get("expected_twin")]
)
def test_a_dead_correction_carries_its_own_twins_row(
    name: str, audit_fix_r1_rows: dict[str, dict[str, Any]]
) -> None:
    """The expected row is recomputed from the twin, not transcribed from analyzer output.

    Each of these sources differs from its twin by a statement whose results nothing reads.
    Deleting such a statement changes nothing a reader could observe, so the two rows have to
    agree.  The equality is asserted three ways: the shipped lane on the row, the oracle pin,
    and the shipped lane on the twin.
    """

    row = _ROWS_BY_NAME[name]
    twin = str(row["expected_twin"])
    assert twin in _SOURCES, name
    observed = _outcome_tuple(audit_fix_r1_rows[name]["outcome"])
    twin_row = _outcome_tuple(audit_fix_r1_rows[twin]["outcome"])
    assert observed == twin_row == _expected_tuple(row)
    assert observed[0] == "candidate"


def test_the_closed_reason_set_is_unchanged_by_round_1() -> None:
    """Round 1 adds no reason: it emits the 3.2 AP path's own consumption reason."""

    assert _CONSUMPTION_REASON in CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS
    assert len(CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS) == 61
    assert core35._MT35_CONSUMPTION_REASON == _CONSUMPTION_REASON
    assert lane35._CONSUMPTION_REASON == _CONSUMPTION_REASON
    for row in _ROWS:
        if row["expected_outcome"] == "abstain":
            assert str(row["expected_reason"]) in CLOSED_MULTIPLE_TESTING_ABSTENTION_REASONS


def test_the_2026_08_29_ap_consumption_gate_still_uses_the_same_reason() -> None:
    """The reason is inherited from the 3.2 fix, so the two gates cannot drift apart."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_2 as ap32,
    )

    source = Path(ap32.__file__).read_text(encoding="utf-8")
    assert "conclusion-consumption" in source


# --- the seven named mutation kills ----------------------------------------------------------


def _row(name: str) -> tuple[str, str, tuple[int, ...], int | None]:
    case_key, source = _SOURCES[name]
    outcome, _census = _run_v35(case_key, source)
    return _outcome_tuple(outcome)


_CLEARED = ("covered", "complete", (0, 1, 2, 3, 4), 5)
_ACCUSED = ("candidate", "none", (), 5)
_REFUSED = ("abstain", _CONSUMPTION_REASON, (), None)

_KILL_A_ROWS = (
    "codex-blocker-1-e18n1-format-arms-on-raw-p",
    "codex-blocker-2-e18p3-dead-library-call",
    "codex-blocker-3-e18p3-dead-call-string-group-tokens",
    "codex-blocker-4-e15p3-dead-library-call",
    "custodian-n1-raw-plain-arms",
    "adversarial-outputs-loaded-only-into-a-display",
)


def test_kill_1_dropping_both_rules_readmits_every_reproducer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: every recognised library correction counts as consumed, and the clearance
    refusal is removed.

    Apply the mutant, confirm all four audit reproducers and both raw-arm probes clear again,
    revert, and confirm the accusation returns.  Recorded: with both rules gone the exact
    false clearance the audit demonstrated is back, on all six rows at once.
    """

    for name in _KILL_A_ROWS:
        assert _row(name) == _expected_tuple(_ROWS_BY_NAME[name]), name
    with monkeypatch.context() as patch:
        patch.setattr(
            core35._MtEngine,
            "_consumed_correction_calls",
            lambda self: set(self.accepted_correction_calls),
        )
        patch.setattr(core35._MtEngine, "_mt35_clearance_refusal", lambda self, *a, **k: None)
        for name in _KILL_A_ROWS:
            assert _row(name) == _CLEARED, name
    for name in _KILL_A_ROWS:
        assert _row(name) == _expected_tuple(_ROWS_BY_NAME[name]), name


def test_kill_1b_dropping_rule_a_alone_costs_the_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: rule A alone is removed, rule B kept.

    Recorded: rule B holds the clearance line on its own, so no false clearance comes back --
    but all six rows abstain instead of accusing.  Rule A is what turns the refusal into the
    row the source's own dead-statement-free twin already carries, which is the answer a
    reader is owed.
    """

    with monkeypatch.context() as patch:
        patch.setattr(
            core35._MtEngine,
            "_consumed_correction_calls",
            lambda self: set(self.accepted_correction_calls),
        )
        for name in _KILL_A_ROWS:
            assert _row(name)[0] == "abstain", name
        assert _row("custodian-n1-control") == _CLEARED, "the control never moves"
    for name in _KILL_A_ROWS:
        assert _row(name) == _expected_tuple(_ROWS_BY_NAME[name]), name


def test_kill_2_counting_a_display_load_as_consumption_readmits_the_display_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: rule A stops excluding loads inside registered sink payloads.

    Recorded: without the display exclusion, a program that prints both correction arrays and
    still decides from the raw p-value is no longer proved dead.  The row stops being an
    accusation and the whole point of the exclusion is that showing a value is not using it.
    """

    name = "adversarial-outputs-loaded-only-into-a-display"
    assert _row(name) == _ACCUSED
    real = core35._MtEngine._consumed_correction_calls

    def without_display_exclusion(self: Any) -> set[ast.Call]:
        consumed: set[ast.Call] = set()
        for node in core35._walk_statements((*self.original_scope, *self.scope)):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                bound = self.correction_return_names.get(node.id)
                if bound is not None:
                    consumed.add(bound[0].call)
        return consumed

    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_consumed_correction_calls", without_display_exclusion)
        assert _row(name) != _ACCUSED
        assert _row("custodian-n1-control") == _CLEARED, "the control never moves"
    assert core35._MtEngine._consumed_correction_calls is real
    assert _row(name) == _ACCUSED


def test_kill_3_dropping_rule_b_readmits_the_printed_reject_false_clearance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: every conclusion position counts as consuming.

    Recorded: rule A cannot reach this row, because the loop's own zip loads the adjusted
    array.  Without rule B the clearance comes straight back, and it is a false one: every
    printed verdict is a raw p-value compared with the threshold.
    """

    name = "adversarial-reject-printed-verdict-from-raw-p"
    assert _row(name) == _REFUSED
    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_mt35_clearance_refusal", lambda self, *a, **k: None)
        assert _row(name) == _CLEARED
        assert _row("custodian-n1-control") == _CLEARED, "the control never moves"
    assert _row(name) == _REFUSED


def test_kill_4_dropping_the_lane_probe_readmits_the_inherited_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the lane returns a frozen 3.4 clearance without probing the 3.5 core.

    Recorded: the route is inherited, and the shipped 3.4 lane clears both of these rows.  A
    consumption proof living only in the 3.5 core is unreachable for them, because the
    ordering rule answers them at step 2.
    """

    for name in ("custodian-n1-raw-plain-arms", "adversarial-reject-printed-verdict-from-raw-p"):
        assert _row(name) != _CLEARED
    with monkeypatch.context() as patch:
        patch.setattr(lane35, "_consumption_narrowed", lambda *a, **k: None)
        assert _row("custodian-n1-raw-plain-arms") == _CLEARED
        assert _row("adversarial-reject-printed-verdict-from-raw-p") == _CLEARED
    assert _row("custodian-n1-raw-plain-arms") == _ACCUSED
    assert _row("adversarial-reject-printed-verdict-from-raw-p") == _REFUSED


def test_kill_5_scanning_only_the_normalised_tree_costs_a_true_accusation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: rule A reads the normalised statements only.

    Recorded as a cost, not a route: `E17:P5` writes a correct partial Holm adjustment whose
    load of the adjusted array survives only in the original statements, so a normalised-only
    scan calls a live correction dead and turns a `strict_subset` accusation into a `none`.
    """

    key = "E17:P5:f3217e701e0f2452afab"
    values = _INPUTS(_REFERENCE_CASE(key), None)
    content = cast(bytes, values.pop("content"))
    before = _outcome_tuple(_CLASSIFY(analyze_v35(content, **values)))
    assert before == ("candidate", "strict_subset", (2, 3), 8)
    real = core35._MtEngine._consumed_correction_calls

    def normalised_only(self: Any) -> set[ast.Call]:
        payload_nodes = {
            id(item)
            for sink in self.sinks
            for payload in sink.payloads
            for item in ast.walk(payload)
        }
        consumed: set[ast.Call] = set()
        for node in core35._walk_statements(self.scope):
            if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)):
                continue
            if id(node) in payload_nodes:
                continue
            bound = self.correction_return_names.get(node.id)
            if bound is not None:
                consumed.add(bound[0].call)
        return consumed

    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_consumed_correction_calls", normalised_only)
        values = _INPUTS(_REFERENCE_CASE(key), None)
        content = cast(bytes, values.pop("content"))
        assert _outcome_tuple(_CLASSIFY(analyze_v35(content, **values))) == (
            "candidate",
            "none",
            (),
            8,
        )
    assert core35._MtEngine._consumed_correction_calls is real
    values = _INPUTS(_REFERENCE_CASE(key), None)
    content = cast(bytes, values.pop("content"))
    assert _outcome_tuple(_CLASSIFY(analyze_v35(content, **values))) == before


def test_kill_6_applying_rule_b_to_a_strict_subset_costs_two_true_accusations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: rule B is applied to every classification instead of to the clearance.

    Recorded as the reason the pairing of rule B with `complete` is deliberate.  `E13:P5` and
    `E17:P5` both carry a real partial correction the proof cannot follow through the loop
    normalisation, and a rule B that looked at them would drop two true accusations without
    closing a single false clearance.
    """

    keys = {
        "E13:P5:80091f37c722eba28e18": ("candidate", "strict_subset", (0, 1), 7),
        "E17:P5:f3217e701e0f2452afab": ("candidate", "strict_subset", (2, 3), 8),
    }

    def measure(key: str) -> tuple[str, str, tuple[int, ...], int | None]:
        values = _INPUTS(_REFERENCE_CASE(key), None)
        content = cast(bytes, values.pop("content"))
        return _outcome_tuple(_CLASSIFY(analyze_v35(content, **values)))

    for key, expected in keys.items():
        assert measure(key) == expected

    def every_classification(
        self: Any,
        classification: str,
        family: set[int],
        library_positions: frozenset[int],
        conclusion_origins: Any,
    ) -> str | None:
        if classification == "none":
            return None
        if library_positions and any(
            core35._mt35_position_state(conclusion_origins.get(position, frozenset()))
            != "consuming"
            for position in library_positions
        ):
            return _CONSUMPTION_REASON
        return None

    with monkeypatch.context() as patch:
        patch.setattr(core35._MtEngine, "_mt35_clearance_refusal", every_classification)
        for key in keys:
            assert measure(key) != keys[key], key
            assert measure(key)[0] == "abstain", key
        assert _row("custodian-n1-control") == _CLEARED, "the control never moves"
    for key, expected in keys.items():
        assert measure(key) == expected
