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

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen_v3
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_4 import (
    _CLOSED_REASONS,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_4 import (
    ADMISSION_KINDS,
    admission_census,
    admission_spans,
    recording_admissions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_comprehension_v3_4 import (
    admitted_comprehensions,
    module_sequences,
    normalize_comprehensions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
    _ENUMERATE_COUNTER,
    _complete_rows,
    _enumerate_is_the_unshadowed_builtin,
    _module_sequences,
    _positions_for,
    _static_bool,
    admitted_caps,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v33,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v34,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_4/prototype-sweep").resolve()
_PINNED = {
    "instrument_results.json": "ee90ff2717d244cffd5faa6372a0fe04f81d28d2c76044ced9317b2756168c86",
    "results.json": "2bf626534a513e951e1c8a559a2538594f6dbb60e6bfda8e0787e0cd704a3cf2",
    "MANIFEST.json": "e4236167657801613b79f55b1a57edeef770da4f3fdf0bf261d6f1673ff15790",
}
_P3_KEY = "E17:P3:a2e031f79e31c80fd900"
_P6_KEY = "E17:P6:b4e507c4b55954752f14"

# The two correct-analysis rows on which the final implementation is deliberately STRICTER than
# the design prototype.  The prototype spliced normalized source text, so its AP recognizer read
# the normalized bytes; production supplies the normalization as a graph fact only and never
# rewrites source, so its AP recognizer reads the original bytes and the fold is not resolved.
# Both rows stay non-candidates and byte-identical to their frozen 3.3 abstention, which is the
# safe direction of the asymmetric prototype/final fidelity rule in design section 0.3.
_STRICTER_THAN_PROTOTYPE = {
    "correct-comprehension-corrected-family": ["abstain", "unresolved-decision-threshold"],
    "correct-terminal-verdict-rebound-into-name": ["abstain", "unresolved-decision-threshold"],
}

_previous_harness = sys.modules.pop("harness", None)
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
    _harness_module = types.ModuleType("harness")
    _harness_module.__dict__.update(_harness)
    sys.modules["harness"] = _harness_module
    _catalog = runpy.run_path(str(_ROOT / "fixture_catalog.py"))
    _FIXTURES = tuple(_catalog["all_fixtures"]())
    _NEW_FIXTURE_NAMES = frozenset(item.name for item in _catalog["new_fixtures"]())
finally:
    sys.modules.pop("harness", None)
    if _previous_harness is not None:
        sys.modules["harness"] = _previous_harness

_REFERENCE_CASE = cast(Callable[[str], Any], _harness["reference_case"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])
_CLASSIFY = cast(Callable[[MultipleTestingDataflowResult], Any], _harness["classify"])
_RESULTS = json.loads((_ROOT / "results.json").read_text(encoding="utf-8"))
_PROTOTYPE_FIXTURE_ROWS = {row["name"]: row for row in _RESULTS["fixtures"]}
_INSTRUMENT = json.loads((_ROOT / "instrument_results.json").read_text(encoding="utf-8"))

# The round-1 audit-fix oracle lives outside the prototype sweep, whose manifest bytes are
# pinned above and may not carry a post-hoc fixture.
_AUDIT_FIX_ROOT = Path(
    "evaluation/development/multitest-code-slice-v3_4/audit-fix-r1-oracle"
).resolve()
_AUDIT_FIX_SOURCES = cast(
    "dict[str, tuple[str, bytes]]",
    runpy.run_path(str(_AUDIT_FIX_ROOT / "fixture_sources.py"))["fixture_sources"](),
)
_AUDIT_FIX_ORACLE = json.loads((_AUDIT_FIX_ROOT / "EXPECTED_ROWS.json").read_text(encoding="utf-8"))
_AUDIT_FIX_ROWS = cast("list[dict[str, Any]]", _AUDIT_FIX_ORACLE["rows"])
_AUDIT_FIX_ROWS_BY_NAME = {str(row["fixture_name"]): row for row in _AUDIT_FIX_ROWS}
_MUTATED_SEQUENCE_ROWS = (
    "correct-ap-selection-sequence-direct-extend",
    "correct-ap-selection-sequence-alias-extend",
    "correct-ap-selection-sequence-alias-augmented-assign",
    "correct-ap-selection-sequence-alias-slice-assign",
)
_SHADOWED_ENUMERATE_ROWS = (
    "shadowed-enumerate-definition-agreeing",
    "correct-ap-shadowed-enumerate-definition-diverging",
)


def _outcome_tuple(value: Any) -> tuple[str, str, tuple[int, ...], int | None]:
    return (
        value.state,
        value.reason_or_classification,
        tuple(value.corrected_positions),
        value.authorized_count,
    )


def _run_source(case_key: str, source: bytes) -> tuple[Any, dict[str, int]]:
    """Execute the shipped 3.4 analyzer once and return its outcome and admission census."""

    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    with recording_admissions():
        result = analyze_v34(content, **values)
        census = admission_census()
    return _CLASSIFY(result), census


def _run_v33(case_key: str, source: bytes) -> Any:
    values = _INPUTS(_REFERENCE_CASE(case_key), source)
    content = cast(bytes, values.pop("content"))
    return _CLASSIFY(analyze_v33(content, **values))


@pytest.fixture(scope="module")
def executed_rows() -> dict[str, dict[str, Any]]:
    """Execute every one of the 245 fixture sources through the real shipped 3.4 analyzer."""

    rows: dict[str, dict[str, Any]] = {}
    for fixture in _FIXTURES:
        outcome, census = _run_source(fixture.case_key, fixture.source)
        rows[fixture.name] = {
            "fixture": fixture,
            "outcome": outcome,
            "census": census,
            "json": outcome.as_json(),
        }
    return rows


def test_pinned_prototype_evidence_is_immutable() -> None:
    assert {
        name: hashlib.sha256((_ROOT / name).read_bytes()).hexdigest() for name in _PINNED
    } == _PINNED


def test_fixture_census_and_correct_analysis_populations_are_exact() -> None:
    assert len(_FIXTURES) == 245
    assert len(_NEW_FIXTURE_NAMES) == 42
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
        "comprehension-positive": 3,
        "comprehension-adversary": 11,
        "comprehension-fa-control": 2,
        "terminal-ifexp-rejected-grammar": 3,
        "iterator-positive": 3,
        "iterator-adversary": 5,
        "iterator-fa-control": 3,
        "cap-positive": 1,
        "cap-adversary": 8,
        "cap-fa-control": 1,
        "reason-routing-adversary": 2,
    }
    assert sum(item.correct_analysis for item in _FIXTURES) == 194
    assert sum(item.correct_analysis for item in _FIXTURES if item.name in _NEW_FIXTURE_NAMES) == 11


@pytest.mark.parametrize("name", [item.name for item in _FIXTURES])
def test_all_245_fixture_rows_execute(name: str, executed_rows: dict[str, dict[str, Any]]) -> None:
    row = executed_rows[name]
    expected = _STRICTER_THAN_PROTOTYPE.get(name, _PROTOTYPE_FIXTURE_ROWS[name]["outcome"])
    assert row["json"] == expected


@pytest.mark.parametrize("name", sorted(_STRICTER_THAN_PROTOTYPE))
def test_named_strictness_residual_is_never_an_accusation(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """The two rows where production abstains and the prototype covered stay non-candidates.

    The gate is directional: if production ever became looser than this pin, or produced a
    candidate here, the assertion fails.  A `covered` prototype row and an `abstain` production
    row are both non-accusations, and production's row is byte-identical to frozen 3.3.
    """

    row = executed_rows[name]
    fixture = row["fixture"]
    assert fixture.correct_analysis is True
    assert _PROTOTYPE_FIXTURE_ROWS[name]["outcome"][0] == "covered"
    assert row["json"][0] == "abstain"
    assert row["json"] == _STRICTER_THAN_PROTOTYPE[name]
    assert _outcome_tuple(_run_v33(fixture.case_key, fixture.source)) == _outcome_tuple(
        row["outcome"]
    )


@pytest.mark.parametrize("name", [item.name for item in _FIXTURES if item.correct_analysis])
def test_no_correct_analysis_fixture_becomes_a_candidate(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    assert executed_rows[name]["outcome"].state != "candidate"


_REFUSED = tuple(item for item in _FIXTURES if getattr(item, "refused_admission", None) is not None)
_ADMITTED = tuple(item for item in _FIXTURES if getattr(item, "admitted", None) is not None)


@pytest.mark.parametrize("fixture", _REFUSED, ids=lambda item: item.name)
def test_named_disqualifiers_refuse_their_admission(
    fixture: Any, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """A disqualifier is proved by an empty admission census, not by a downstream abstention.

    The non-vacuity half matters just as much: a fixture whose shipped 3.3 baseline already
    classifies would have an empty census for free, because the ordering rule attempts no 3.4
    admission on a classified row.
    """

    baseline = _run_v33(fixture.case_key, fixture.source)
    assert baseline.state == "abstain", "the disqualifier assertion would be vacuous"
    census = executed_rows[fixture.name]["census"]
    assert census[fixture.refused_admission] == 0


@pytest.mark.parametrize("fixture", _ADMITTED, ids=lambda item: item.name)
def test_named_admissions_actually_fire(
    fixture: Any, executed_rows: dict[str, dict[str, Any]]
) -> None:
    assert executed_rows[fixture.name]["census"][fixture.admitted] > 0


def test_admission_census_totals_and_rows_match_the_executed_design_evidence(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    rows = {
        kind: sorted(name for name, row in executed_rows.items() if row["census"][kind])
        for kind in ADMISSION_KINDS
    }
    expected = {
        kind: sorted(row["name"] for row in _RESULTS["fixtures"] if row["admission_census"][kind])
        for kind in ADMISSION_KINDS
    }
    assert rows == expected
    assert rows["terminal-ifexp"] == []


_POSITIVE_CONTROLS = {
    "positive-comprehension-dict-helper-record": (
        "comprehension",
        ("candidate", "none", (), 6),
    ),
    "positive-ap-enumerate-start-one": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
    "positive-ap-enumerate-no-start": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
    "positive-ap-enumerate-start-zero": (
        "enumerate",
        ("candidate", "strict_subset", (0, 1, 2), 7),
    ),
}


@pytest.mark.parametrize("name", sorted(_POSITIVE_CONTROLS))
def test_positive_controls_admit_and_reach_their_pinned_outcome(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    kind, expected = _POSITIVE_CONTROLS[name]
    row = executed_rows[name]
    assert row["census"][kind] > 0
    assert _outcome_tuple(row["outcome"]) == expected


def test_min_form_stays_admitted_without_the_cap_admission_firing(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-ap-cap-min-form-unchanged"]
    assert _outcome_tuple(row["outcome"]) == ("candidate", "strict_subset", (0, 1, 2), 7)
    assert row["census"]["cap"] == 0
    assert row["census"]["enumerate"] == 1


def test_if_cap_and_min_spellings_produce_identical_coverage_records(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """Extension D's whole claim: two spellings of the same arithmetic agree exactly."""

    if_cap = executed_rows["correct-ap-cap-complete-correction"]
    minimum = executed_rows["correct-ap-enumerate-complete-correction-min"]
    assert _outcome_tuple(if_cap["outcome"]) == ("covered", "complete", (0, 1, 2, 3, 4, 5, 6), 7)
    assert _outcome_tuple(if_cap["outcome"]) == _outcome_tuple(minimum["outcome"])
    assert if_cap["census"]["cap"] == 1
    assert minimum["census"]["cap"] == 0


def test_list_form_is_admitted_and_its_record_model_residual_is_recorded(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-comprehension-list-form"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].state == "abstain"
    assert row["outcome"].reason_or_classification == "pderived-conclusion-family-incomplete"


def test_inline_flat_record_element_resolves_through_the_global_census(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    row = executed_rows["positive-comprehension-inline-flat-record"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].reason_or_classification == (
        "extra-registered-test-outside-authorized-family"
    )


def test_a_normalized_family_never_hides_a_later_p_gated_test(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """The whole-module census runs on original bytes, so the extra registered call is seen."""

    row = executed_rows["correct-comprehension-gates-later-test"]
    assert row["census"]["comprehension"] == 1
    assert row["outcome"].state == "abstain"
    assert row["outcome"].reason_or_classification == "authorized-family-test-census-incomplete"


# --------------------------------------------------------------------------------------
# Extension A grammar, at the grammar's own gate
# --------------------------------------------------------------------------------------


def _fixture(name: str) -> Any:
    return next(item for item in _FIXTURES if item.name == name)


def _outcome_columns(case_key: str, source: bytes) -> tuple[str, ...]:
    return tuple(_INPUTS(_REFERENCE_CASE(case_key), source)["outcome_columns"])


@pytest.mark.parametrize(
    "name",
    [
        "correct-comprehension-with-filter",
        "correct-comprehension-over-non-contract-sequence",
        "correct-comprehension-key-not-loop-variable",
        "correct-comprehension-two-generators",
        "correct-comprehension-conditional-element",
        "correct-comprehension-nested-element",
        "correct-comprehension-keyword-argument-element",
        "correct-comprehension-out-of-contract-order",
        "correct-comprehension-target-rebound",
        "correct-comprehension-collection-mutated",
        "correct-comprehension-element-ignores-loop-variable",
    ],
)
def test_comprehension_disqualifiers_refuse_at_the_grammar_gate(name: str) -> None:
    """Mutation kill: admitting a filtered or otherwise disqualified comprehension here fails."""

    fixture = _fixture(name)
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    assert admitted_comprehensions(tree, columns) == ()
    assert normalize_comprehensions(fixture.source, columns) is None


def test_the_pinned_p3_comprehension_is_admitted_with_its_exact_structural_evidence() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    admitted = admitted_comprehensions(ast.parse(fixture.source), columns)
    assert len(admitted) == 1
    item = admitted[0]
    assert item.kind == "dict"
    assert item.element_kind == "call"
    assert item.target == "results"
    assert item.sequence_name == "OUTCOMES"
    assert item.loop_variable == "outcome"
    assert module_sequences(ast.parse(fixture.source))["OUTCOMES"] == columns


def test_lowering_is_graph_preserving_and_idempotent() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    original = ast.parse(fixture.source)
    admitted = admitted_comprehensions(original, columns)
    element_dump = ast.dump(admitted[0].element, include_attributes=True)

    first = normalize_comprehensions(fixture.source, columns)
    second = normalize_comprehensions(fixture.source, columns)
    assert first is not None and second is not None
    assert ast.dump(first.tree, include_attributes=True) == ast.dump(
        second.tree, include_attributes=True
    )
    assert first.admissions == second.admissions

    # The lowered element is the same graph as the original element.
    lowered_loop = next(
        node
        for node in ast.walk(first.tree)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == "OUTCOMES"
    )
    stored = lowered_loop.body[0]
    assert isinstance(stored, ast.Assign)
    assert ast.dump(stored.value, include_attributes=True) == element_dump

    # An already-normalized module admits nothing and lowers to itself.
    assert admitted_comprehensions(first.tree, columns) == ()


def test_normalization_produces_a_graph_fact_and_leaves_the_source_bytes_alone() -> None:
    fixture = _fixture("positive-comprehension-dict-helper-record")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    normalization = normalize_comprehensions(fixture.source, columns)
    assert normalization is not None
    assert isinstance(normalization.tree, ast.Module)
    assert fixture.source == _fixture("positive-comprehension-dict-helper-record").source


# --------------------------------------------------------------------------------------
# Extension C: the counter is opaque
# --------------------------------------------------------------------------------------


def test_enumerate_counter_binding_is_opaque_to_static_bool_and_positions() -> None:
    """Mutation kill: binding the counter to an int makes `_static_bool` resolve and admits it."""

    fixture = _fixture("positive-ap-enumerate-start-one")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and loop in ast.walk(node)
    )
    with recording_admissions():
        rows = _complete_rows(
            loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
        )
        assert admission_census()["enumerate"] == 1
    assert rows is not None and len(rows) == len(columns)
    assert tuple(row["outcome"] for row in rows) == columns
    assert all(row["position"] is _ENUMERATE_COUNTER for row in rows)
    assert not isinstance(_ENUMERATE_COUNTER, bool)
    assert _ENUMERATE_COUNTER not in columns

    counter_guard = ast.parse("position <= 3", mode="eval").body
    for row in rows:
        assert _static_bool(counter_guard, row, owner=owner, sequences=sequences) is None
        assert (
            _static_bool(
                ast.Name(id="position", ctx=ast.Load()),
                row,
                owner=owner,
                sequences=sequences,
            )
            is None
        )


def test_counter_use_in_a_decision_admits_the_row_table_and_still_refuses(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    decision = executed_rows["correct-ap-counter-used-in-decision"]
    factor = executed_rows["correct-ap-counter-used-as-factor"]
    assert decision["census"]["enumerate"] == 1
    assert decision["outcome"].state == "abstain"
    assert decision["outcome"].reason_or_classification == "unresolved-manual-correction-present"
    assert factor["outcome"].state == "abstain"
    assert factor["outcome"].reason_or_classification == "unresolved-manual-correction-present"


def test_positions_refuse_when_a_branch_is_guarded_on_the_counter() -> None:
    fixture = _fixture("correct-ap-counter-used-in-decision")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    guard = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "position"
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and guard in ast.walk(node)
    )
    target = guard.body[0]
    with recording_admissions():
        assert (
            _positions_for(
                target,
                tree=tree,
                owner=owner,
                parents=parents,
                sequences=sequences,
                outcome_columns=columns,
            )
            is None
        )


def test_a_membership_guard_on_the_counter_can_never_select_positions() -> None:
    """Mutation kill: bind the counter to a row value the predicates can read and this resolves.

    A membership test is the one comparison form `_static_bool` can decide, so it is the exact
    shape that would let a counter select family positions if the binding were transparent.
    """

    fixture = _fixture("positive-ap-enumerate-start-one")
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
    )
    owner = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and loop in ast.walk(node)
    )
    with recording_admissions():
        rows = _complete_rows(
            loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
        )
    assert rows is not None
    counter_membership = ast.parse("position in MUSCULOSKELETAL", mode="eval").body
    outcome_membership = ast.parse("outcome in MUSCULOSKELETAL", mode="eval").body
    counter_values = [
        _static_bool(counter_membership, row, owner=owner, sequences=sequences) for row in rows
    ]
    outcome_values = [
        _static_bool(outcome_membership, row, owner=owner, sequences=sequences) for row in rows
    ]
    # The outcome element decides.  The counter is never a member of any contract name set, so
    # a membership guard on it selects the empty set on every row and can never carve a family.
    assert outcome_values == [True, True, True, False, False, False, False]
    assert counter_values == [False] * len(rows)
    assert len(set(counter_values)) == 1


@pytest.mark.parametrize(
    "name",
    [
        "correct-ap-enumerate-over-non-contract-sequence",
        "correct-ap-enumerate-over-zip",
        "correct-ap-enumerate-single-target",
        "correct-ap-enumerate-nonliteral-start",
        "correct-ap-enumerate-reversed-sequence",
    ],
)
def test_enumerate_disqualifiers_refuse_at_the_row_table_gate(name: str) -> None:
    """Mutation kill: admitting a non-bare-Name or non-literal-start iterator fails here."""

    fixture = _fixture(name)
    columns = _outcome_columns(fixture.case_key, fixture.source)
    tree = ast.parse(fixture.source)
    sequences = _module_sequences(tree)
    owner = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    with recording_admissions():
        for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
            _complete_rows(
                loop, tree=tree, owner=owner, sequences=sequences, outcome_columns=columns
            )
        assert admission_census()["enumerate"] == 0


# --------------------------------------------------------------------------------------
# Extension D: the adjacent if-cap
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "correct-ap-cap-non-adjacent",
        "correct-ap-cap-guard-on-different-name",
        "correct-ap-cap-guard-not-literal-one",
        "correct-ap-cap-body-extra-statement",
        "correct-ap-cap-with-else",
        "correct-ap-cap-assigns-other-value",
        "correct-ap-cap-augmented-reassignment",
        "correct-ap-cap-reassigns-other-name",
    ],
)
def test_cap_disqualifiers_refuse_at_the_cap_grammar_gate(name: str) -> None:
    """Mutation kill: dropping the adjacency, guard, or sole-statement proof admits these."""

    fixture = _fixture(name)
    assert admitted_caps(ast.parse(fixture.source)) == ()


def test_the_pinned_p6_cap_is_admitted_with_its_exact_shape() -> None:
    fixture = _fixture("positive-ap-enumerate-start-one")
    caps = admitted_caps(ast.parse(fixture.source))
    assert len(caps) == 1
    cap = caps[0]
    assert cap.name == "corrected_p"
    assert isinstance(cap.product.value, ast.BinOp)
    assert isinstance(cap.guard.test, ast.Compare)
    assert cap.guard.orelse == []
    assert cap.guard.body == [cap.reassignment]


@pytest.mark.parametrize("form", ["X > 1.0", "X >= 1.0", "1.0 < X", "1.0 <= X"])
def test_all_four_admitted_cap_comparison_forms_are_one_fold(form: str) -> None:
    source = (
        f"def main():\n    X = raw * factor\n    if {form}:\n        X = 1.0\n    print(X)\n"
    ).encode()
    caps = admitted_caps(ast.parse(source))
    assert len(caps) == 1
    assert caps[0].name == "X"


# --------------------------------------------------------------------------------------
# Extension B is specified and NOT shipped; extension E is measured and NOT applied
# --------------------------------------------------------------------------------------


def test_extension_b_is_not_in_the_shipped_recognizer_set(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """No 3.4 module widens the terminal-`IfExp` proof, and no row admits a position."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )
    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_4 as dataflow

    for module in (comprehension, correction, dataflow):
        text = Path(module.__file__ or "").read_text(encoding="utf-8")
        assert "_terminal_ifexp_positions" not in text
        assert "_reaches_print" not in text
        assert "_dict_field_for_name" not in text
    # The only terminal-presentation entry point 3.4 uses is the byte-frozen 3.3 proof.
    dataflow_text = Path(dataflow.__file__ or "").read_text(encoding="utf-8")
    assert "code_csv_multiple_testing_terminal_presentation_v3_3" in dataflow_text
    assert "prove_terminal_presentation" in dataflow_text
    assert all(row["census"]["terminal-ifexp"] == 0 for row in executed_rows.values())


@pytest.mark.parametrize(
    "name",
    [
        "correct-terminal-verdict-stored-then-printed",
        "correct-terminal-verdict-rebound-into-name",
        "correct-terminal-verdict-returned-from-helper",
    ],
)
def test_the_specified_section_5_verdict_store_shapes_stay_refused(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """The three named store shapes remain non-candidates and admit no terminal position."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
        prove_terminal_presentation,
    )

    fixture = _fixture(name)
    assert prove_terminal_presentation(fixture.source) is None
    row = executed_rows[name]
    assert row["census"]["terminal-ifexp"] == 0
    assert row["outcome"].state != "candidate"
    probe = {
        item["fixture"]: item["v34_admitted_positions"]
        for item in _INSTRUMENT["terminal_ifexp_refusal_probe"]["rows"]
    }
    assert probe[name] == []


def test_e16_p4_keeps_its_pinned_candidate_under_the_shipped_recognizer_set() -> None:
    """The measured extension-B collision is the reason B is not shipped; the pin holds."""

    key = "E16:P4:9ced761b41ef93485acf"
    case = _REFERENCE_CASE(key)
    outcome, census = _run_source(key, case.source_path.read_bytes())
    assert _outcome_tuple(outcome) == ("candidate", "none", (), 7)
    assert census["terminal-ifexp"] == 0
    collision = next(
        row for row in _INSTRUMENT["extension_b_collision_probe"]["rows"] if row["case_key"] == key
    )
    assert collision["extension_b_regresses_row"] is True
    assert collision["outcome_with_extension_b"] == ["abstain", "hierarchical-gatekeeping-present"]


@pytest.mark.parametrize(
    "name", ["correct-outcome-headers-genuine-screen", "correct-outcome-headers-early-exit"]
)
def test_genuine_gatekeeping_keeps_its_reason_and_admits_no_comprehension(
    name: str, executed_rows: dict[str, dict[str, Any]]
) -> None:
    """Extension E is not applied: no reason string is routed anywhere in 3.4."""

    row = executed_rows[name]
    assert row["census"]["comprehension"] == 0
    assert row["outcome"].state == "abstain"
    assert (
        row["outcome"].reason_or_classification
        == _run_v33(row["fixture"].case_key, row["fixture"].source).reason_or_classification
    )


def test_no_row_anywhere_emits_the_specified_reason_routing(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """The ten measured relabel rows keep `hierarchical-gatekeeping-present` unchanged."""

    measured = sorted(
        row["name"]
        for row in _RESULTS["fixtures"]
        if row["outcome_with_reason_routing"] != row["outcome"]
    )
    assert len(measured) == 10
    for name in measured:
        row = executed_rows[name]
        assert row["json"] == _PROTOTYPE_FIXTURE_ROWS[name]["outcome"]
        assert row["outcome"].reason_or_classification != "pvalue-control-dependence-unresolved"
    assert [row["key"] for row in _RESULTS["cases"] if row["relabeled"]] == []


# --------------------------------------------------------------------------------------
# The ordering rule
# --------------------------------------------------------------------------------------


def test_a_row_the_frozen_pipeline_classifies_is_returned_untouched() -> None:
    """Step 3: no 3.4 admission is even attempted on a frozen 3.3 classification."""

    key = "E16:P3:5a9c5b4377c33916d672"
    case = _REFERENCE_CASE(key)
    source = case.source_path.read_bytes()
    frozen = _run_v33(key, source)
    outcome, census = _run_source(key, source)
    assert frozen.state == "candidate"
    assert _outcome_tuple(outcome) == _outcome_tuple(frozen)
    assert census == dict.fromkeys(ADMISSION_KINDS, 0)


#: Rows where the 3.4 re-analysis reaches a DIFFERENT wall than the frozen 3.3 pipeline did.
#: These are the rows on which the ordering rule is load-bearing rather than decorative: if the
#: dataflow adopted the re-analysis abstention, every one of these public reasons would change.
_REANALYSIS_DIVERGES = {
    "positive-comprehension-list-form": (
        "pderived-conclusion-family-incomplete",
        "test-battery-cardinality-unresolved",
    ),
    "correct-helper-record-mutates-nonlocal-state": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-conclusion-recomputed-from-raw-p": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-conditional-store": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-nested-record": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
    "correct-helper-record-unresolved-consumer": (
        "unresolved-pvalue-consumer",
        "pderived-conclusion-family-incomplete",
    ),
}


@pytest.mark.parametrize("name", sorted(_REANALYSIS_DIVERGES))
def test_an_abstaining_reanalysis_returns_the_frozen_reason_byte_for_byte(name: str) -> None:
    """Step 5: a 3.4 re-analysis that abstains never replaces the frozen 3.3 reason.

    Mutation kill: letting the 3.4 dataflow adopt a re-analysis abstention reason changes the
    emitted reason on exactly these rows, because the re-analysis really does reach a different
    wall.  The pinned pair records both reasons, so the assertion cannot pass by accident.
    """

    from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
        _reanalyze_with_v34_admissions,
    )

    frozen_reason, reanalysis_reason = _REANALYSIS_DIVERGES[name]
    fixture = _fixture(name)
    values = _INPUTS(_REFERENCE_CASE(fixture.case_key), fixture.source)
    content = cast(bytes, values.pop("content"))

    assert _run_v33(fixture.case_key, fixture.source).reason_or_classification == frozen_reason
    with recording_admissions():
        attempted = _CLASSIFY(_reanalyze_with_v34_admissions(content, **values))
        census = admission_census()
    assert census["comprehension"] == 1, "the re-analysis really did run and admit"
    assert attempted.state == "abstain"
    assert attempted.reason_or_classification == reanalysis_reason
    assert reanalysis_reason != frozen_reason

    shipped, _shipped_census = _run_source(fixture.case_key, fixture.source)
    assert shipped.state == "abstain"
    assert shipped.reason_or_classification == frozen_reason


def test_every_frozen_3_3_abstention_reason_survives_across_the_new_fixture_rows(
    executed_rows: dict[str, dict[str, Any]],
) -> None:
    """No new fixture row that stays an abstention may carry a reason 3.3 did not emit."""

    for name in sorted(_NEW_FIXTURE_NAMES):
        row = executed_rows[name]
        if row["outcome"].state != "abstain":
            continue
        frozen = _run_v33(row["fixture"].case_key, row["fixture"].source)
        assert frozen.state == "abstain", name
        assert row["outcome"].reason_or_classification == frozen.reason_or_classification, name


# --------------------------------------------------------------------------------------
# Observed trigger attribution, closed reasons, and frozen anchors
# --------------------------------------------------------------------------------------


def test_the_real_guard_attribution_at_the_e17_p3_control_is_outcome_headers_only() -> None:
    """Run the shipped hierarchy guard and record every control it actually tracked."""

    case = _REFERENCE_CASE(_P3_KEY)
    values = _INPUTS(case, None)
    content = cast(bytes, values.pop("content"))
    observed: list[dict[str, Any]] = []
    original_control = frozen_v3._MtEngine._control_tracked
    original_guard = frozen_v3._MtEngine._hierarchy_guard
    registry: dict[int, set[int]] = {}

    def _registry_expressions(scope: tuple[Any, ...]) -> set[int]:
        result: set[int] = set()
        for node in frozen_v3._walk_statements(scope):
            if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
                result.add(id(node.test))
            elif isinstance(node, ast.Match):
                result.add(id(node.subject))
                result.update(id(item.guard) for item in node.cases if item.guard is not None)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                result.add(id(node.iter))
            elif isinstance(node, ast.comprehension):
                result.add(id(node.iter))
                result.update(id(item) for item in node.ifs)
        return result

    state = {"active": False}

    def control(self: Any, node: ast.expr, **kwargs: Any) -> bool:
        tracked = original_control(self, node, **kwargs)
        if state["active"] and tracked:
            if id(self) not in registry:
                registry[id(self)] = _registry_expressions((*self.original_scope, *self.scope))
            observed.append(
                {
                    "position": list(
                        (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
                    ),
                    "node_type": type(node).__name__,
                    "p_origins": len(self._p_origins(node)),
                    "correction_control": bool(self._correction_control_present(node)),
                    "outcome_headers": sorted(self._outcome_headers(node, set(), 0)),
                    "registry_control": id(node) in registry[id(self)],
                }
            )
        return tracked

    def guard(self: Any) -> str | None:
        state["active"] = True
        try:
            return original_guard(self)
        finally:
            state["active"] = False

    frozen_v3._MtEngine._control_tracked = control
    frozen_v3._MtEngine._hierarchy_guard = guard
    try:
        result = analyze_v33(content, **values)
    finally:
        frozen_v3._MtEngine._control_tracked = original_control
        frozen_v3._MtEngine._hierarchy_guard = original_guard

    assert result.reason == "hierarchical-gatekeeping-present"
    assert len(observed) == 1
    control_row = observed[0]
    assert control_row["position"] == [71, 35, 71, 54]
    assert control_row["node_type"] == "Compare"
    assert control_row["p_origins"] == 0
    assert control_row["correction_control"] is False
    assert control_row["registry_control"] is True
    assert control_row["outcome_headers"] == sorted(values["outcome_columns"])
    assert len(control_row["outcome_headers"]) == 6
    pinned = _INSTRUMENT["traces"][0]
    assert pinned["case_key"] == _P3_KEY
    assert pinned["first_tracked_control"]["position"] == [71, 35, 71, 54]
    assert pinned["first_tracked_control"]["p_origins"] == 0


def test_closed_reason_set_remains_exactly_frozen_61() -> None:
    from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_3 import (
        _CLOSED_REASONS as FROZEN_REASONS,
    )

    assert _CLOSED_REASONS == FROZEN_REASONS
    assert len(_CLOSED_REASONS) == 61


def test_frozen_3_1_3_2_3_3_anchor_bytes_are_exact() -> None:
    root = Path(__file__).resolve().parents[1]
    pinned = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3.py": "498bf5c22305270fe64ed1ef73b7ac8a7a2637ce4f64520e8d9ca4ac15166618",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py": "38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py": "b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_3.py": "c82510238b422af746299e9e1c418a0474107d1b57d119fd7dc5685e037edd2e",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_3.py": "d9d919b5289c767a39dd62edea8fc17563a6ad76aa627c49e427b6201f81bf4a",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_3.py": "de46498474b0043231a66b6adeb779e799b3736afce162b6919dc0eebc516242",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_terminal_presentation_v3_3.py": "d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_helper_record_v3_3.py": "f3c5e8fb9ec52f8e2d13a6de11849f63b08a073e4208f9d5936fbcf177c76033",
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_3.py": "7c3ce13e3e10fcf012bf4c803f6a5e3bd88aa30146059873710b8a549550efcc",
        "src/sc_referee/scientific_checks/integration_multiple_testing_v3_3.py": "edc5b3d94329a15c263dbab167bc623be7f778bca5b867d771f9538642719557",
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_3.py": "0b7505fb42d191be0916f287eeea72dfc4d579edbc2a367ec413b503e1670e4c",
        "src/sc_referee/scientific_checks/multiple_testing_scope_questions_v3_3.py": "b060f34c52c64db7f36ca1e2469239e6a6920404ecee87c13e986f526c59ff3b",
        "docs/implementation/MULTITEST-3.3-TERMINAL-PRESENTATION-DESIGN-2026-08-30.md": "cbc37990e9a713c486bf903cefef03c08ad264e7b6112383330b56a0c3f6c224",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/results.json": "be9ddd1ea4b8bd27faff92392865cbb76f14fbf6b162f847523fe5900d1bd7ad",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/MANIFEST.json": "10e94f5a056e50662bfc65bfafc2ebec0ea519a4c7bef1f5269caddf6523bf5f",
        "evaluation/development/multitest-code-slice-v3_3/prototype-sweep/instrument_results.json": "03c7aa815b8728bf9452afe666f9738e9501f345903ce7ef7fe3f520c320134f",
        "evaluation/development/multitest-code-slice-v3_3/adapter_replay_records_v3_3.json": "4b42ee3a517bd95591eac9f0d7bb9a497728f9df708c57fc99298d7205df83ce",
        "evaluation/development/blind-envelope-17-2026-08-30/ROLE_MAP.json": "004a87be3448c1736f24ac48d0deb155694ee7da08670d02918ac8e09d4cea9e",
        "evaluation/development/blind-envelope-17-2026-08-30/AUDIT_RESULTS.json": "ca9cb2caf2b4fd0c4047a7758f0351278f7bd66f79f1dacaf6af0754a47b4b6e",
        "docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md": "2f7bd77e1020777c9fcdc5573edc87c43567ba153fd3fc1f801926752993c854",
    }
    assert {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in pinned
    } == pinned


def test_production_uses_graph_facts_without_source_rewrite_or_monkeypatch() -> None:
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )
    from sc_referee.scientific_checks import code_csv_multiple_testing_dataflow_v3_4 as dataflow

    comprehension_source = Path(comprehension.__file__ or "").read_text(encoding="utf-8")
    dataflow_source = Path(dataflow.__file__ or "").read_text(encoding="utf-8")
    assert "ast.unparse" not in comprehension_source
    assert "ast.unparse" not in dataflow_source
    for text in (comprehension_source, dataflow_source):
        assert "monkeypatch" not in text
        assert "setattr(" not in text
    # The versioned correction model owns the recognizers outright; it never rebinds a frozen one.
    correction_source = Path(correction.__file__ or "").read_text(encoding="utf-8")
    assert "setattr(" not in correction_source
    assert "_COMPLETE_ROWS_V33" not in correction_source

    ordering = inspect.getsource(dataflow.analyze_code_csv_multiple_testing_dataflow)
    assert "_frozen_v33_analyze" in ordering
    assert "return frozen" in ordering


def test_the_admission_census_is_write_only_and_never_reaches_a_proof() -> None:
    """The census records evidence; no recognizer reads it back to decide anything."""

    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_comprehension_v3_4 as comprehension,
    )
    from sc_referee.scientific_checks import (
        code_csv_multiple_testing_correction_model_v3_4 as correction,
    )

    for module in (comprehension, correction):
        text = Path(module.__file__ or "").read_text(encoding="utf-8")
        # The recognizers write to the census and never call either reader back.
        assert "admission_census(" not in text
        assert "admission_spans(" not in text
        assert "record_admission(" in text

    fixture = _fixture("positive-ap-enumerate-start-one")
    inside, census_inside = _run_source(fixture.case_key, fixture.source)
    assert census_inside["enumerate"] == 1
    # Recording outside an open census is ignored, so no count can leak between analyses.
    outside, _ = _run_source(fixture.case_key, fixture.source)
    assert _outcome_tuple(inside) == _outcome_tuple(outside)
    assert set(admission_spans()) == set(ADMISSION_KINDS)


# --------------------------------------------------------------------------------------
# Audit fix round 1: sequence-object stability, the unshadowed builtin, contract order
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def audit_fix_rows() -> dict[str, dict[str, Any]]:
    """Execute every audit-fix source through the shipped 3.4 analyzer and the frozen 3.3 one."""

    rows: dict[str, dict[str, Any]] = {}
    for name, (case_key, source) in _AUDIT_FIX_SOURCES.items():
        outcome, census = _run_source(case_key, source)
        rows[name] = {
            "case_key": case_key,
            "source": source,
            "outcome": outcome,
            "census": census,
            "frozen": _run_v33(case_key, source),
        }
    return rows


def test_audit_fix_round_1_oracle_is_independent_and_source_complete() -> None:
    assert _AUDIT_FIX_ORACLE["provenance"]["implementation_output_used"] is False
    assert len(_AUDIT_FIX_ROWS) == 9
    assert sum(bool(row["correct_analysis"]) for row in _AUDIT_FIX_ROWS) == 4
    assert set(_AUDIT_FIX_ROWS_BY_NAME) == set(_AUDIT_FIX_SOURCES)
    assert {
        name: "sha256:" + hashlib.sha256(source).hexdigest()
        for name, (_case_key, source) in _AUDIT_FIX_SOURCES.items()
    } == {name: str(row["fixture_source_sha256"]) for name, row in _AUDIT_FIX_ROWS_BY_NAME.items()}


@pytest.mark.parametrize("row", _AUDIT_FIX_ROWS, ids=lambda row: row["fixture_name"])
def test_all_9_audit_fix_round_1_rows_execute(
    row: dict[str, Any], audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    observed = audit_fix_rows[str(row["fixture_name"])]
    assert _outcome_tuple(observed["outcome"]) == (
        str(row["expected_outcome"]),
        str(row["expected_reason"]),
        tuple(cast("list[int]", row.get("expected_corrected_positions", []))),
        cast("int | None", row.get("expected_authorized_count")),
    )
    assert observed["census"] == row["expected_admission_census"]
    # Design section 3.3 steps 5 and 6: a refused admission returns the frozen 3.3 row unchanged.
    identical = _outcome_tuple(observed["outcome"]) == _outcome_tuple(observed["frozen"])
    assert identical is bool(row["expected_frozen_v33_identical"])


def test_no_audit_fix_correct_analysis_row_becomes_a_candidate(
    audit_fix_rows: dict[str, dict[str, Any]],
) -> None:
    """The four mutated-sequence rows are complete seven-outcome corrections, never subsets."""

    correct = [row for row in _AUDIT_FIX_ROWS if row["correct_analysis"]]
    assert len(correct) == 4
    assert not [
        str(row["fixture_name"])
        for row in correct
        if audit_fix_rows[str(row["fixture_name"])]["outcome"].state == "candidate"
    ]


@pytest.mark.parametrize("name", _MUTATED_SEQUENCE_ROWS)
def test_mutated_selection_sequence_refuses_at_the_sequence_object_stability_gate(
    name: str,
) -> None:
    """Mutation kill: dropping the object-stability closure readmits the mutated sequence here.

    The accusation this closes is a complete seven-outcome correction reported as a strict
    subset of three, so the assertion is that the mutated sequence never enters the module
    sequence table at all.  A downstream abstention would not distinguish the fix from a
    coincidence.
    """

    row = _AUDIT_FIX_ROWS_BY_NAME[name]
    _case_key, source = _AUDIT_FIX_SOURCES[name]
    unstable = [str(item) for item in row["expected_unstable_sequence_names"]]
    sequences = _module_sequences(ast.parse(source))
    assert [item for item in unstable if item in sequences] == []
    # Non-vacuity: every one of those names resolves on the unmutated source.
    _control_key, control = _AUDIT_FIX_SOURCES["positive-ap-unmutated-sequence-genuine-enumerate"]
    assert set(unstable) <= set(_module_sequences(ast.parse(control)))


@pytest.mark.parametrize("name", _SHADOWED_ENUMERATE_ROWS)
def test_shadowed_enumerate_refuses_at_the_unshadowed_builtin_gate(
    name: str, audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    """Mutation kill: proving the builtin by `node.func.id` alone readmits a project-local def."""

    _case_key, source = _AUDIT_FIX_SOURCES[name]
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == "enumerate" for node in ast.walk(tree)
    )
    assert _enumerate_is_the_unshadowed_builtin(tree) is False
    assert audit_fix_rows[name]["census"]["enumerate"] == 0
    # Non-vacuity: the same predicate admits the genuine builtin on the unaltered source.
    _control_key, control = _AUDIT_FIX_SOURCES["positive-ap-unmutated-sequence-genuine-enumerate"]
    assert _enumerate_is_the_unshadowed_builtin(ast.parse(control)) is True


def test_flat_equal_length_sequence_refuses_at_the_contract_order_equality_gate() -> None:
    """Mutation kill: matching the generator sequence by length instead of order admits this.

    The pinned out-of-contract-order row cannot kill that mutant.  It builds its sequence with
    `list(reversed(OUTCOMES))`, which never resolves to a module sequence, so it refuses before
    the order comparison is reached.  This row resolves, carries the contract length, and
    carries exactly the contract member set, so order equality is the only predicate left.
    """

    name = "correct-comprehension-flat-literal-out-of-contract-order"
    row = _AUDIT_FIX_ROWS_BY_NAME[name]
    case_key, source = _AUDIT_FIX_SOURCES[name]
    columns = _outcome_columns(case_key, source)
    tree = ast.parse(source)
    sequence = module_sequences(tree).get("SHUFFLED")
    upstream = row["expected_upstream_gates_pass"]
    assert (sequence is not None) is upstream["sequence_is_a_resolvable_module_sequence"]
    assert sequence is not None
    assert (len(sequence) == len(columns)) is upstream["sequence_length_equals_contract_length"]
    assert (set(sequence) == set(columns)) is upstream["member_set_equals_contract"]
    assert (tuple(sequence) == columns) is upstream["sequence_order_equals_contract_order"]
    assert admitted_comprehensions(tree, columns) == ()
    assert normalize_comprehensions(source, columns) is None


@pytest.mark.parametrize(
    "name",
    [
        "positive-ap-unmutated-sequence-genuine-enumerate",
        "positive-ap-selection-sequence-alias-without-mutation",
    ],
)
def test_both_narrowings_keep_the_pinned_e17_p6_movement(
    name: str, audit_fix_rows: dict[str, dict[str, Any]]
) -> None:
    """Mutation kill: a closure that refused every sequence, or refused a live alias, loses this."""

    row = audit_fix_rows[name]
    assert _outcome_tuple(row["outcome"]) == ("candidate", "strict_subset", (0, 1, 2), 7)
    assert row["census"]["enumerate"] == 1
    assert row["census"]["cap"] == 1
