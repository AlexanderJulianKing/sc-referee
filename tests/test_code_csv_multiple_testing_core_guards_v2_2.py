from __future__ import annotations

import ast
import csv
import io
import json
import re
import runpy
import tomllib
from collections import Counter
from pathlib import Path

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 as dataflow
from sc_referee.core.ids import canonical_json


def _csv(columns: tuple[str, ...]) -> bytes:
    header = "group," + ",".join(columns) + "\n"
    rows = (
        "a," + ",".join(str(index + 1) for index in range(len(columns))) + "\n"
        "a," + ",".join(str(index + 2) for index in range(len(columns))) + "\n"
        "b," + ",".join(str(index + 4) for index in range(len(columns))) + "\n"
        "b," + ",".join(str(index + 5) for index in range(len(columns))) + "\n"
    )
    return (header + rows).encode()


def _run(
    source: str, columns: tuple[str, ...] = ("m1", "m2", "m3")
) -> dataflow.MultipleTestingDataflowResult:
    return dataflow.analyze_code_csv_multiple_testing_dataflow(
        source.encode(),
        authorized_path="data.csv",
        group_column="group",
        outcome_columns=columns,
        csv_header=("group", *columns),
        group_values=("a", "b"),
        csv_content=_csv(columns),
    )


def _run_fixture(fixture: dict[str, object]) -> dataflow.MultipleTestingDataflowResult:
    source = fixture["source"]
    assert isinstance(source, str)
    corpus_case = fixture.get("corpus_case")
    if corpus_case is None:
        columns = fixture.get("columns", ("m1", "m2", "m3"))
        assert isinstance(columns, tuple)
        return _run(source, columns)
    assert isinstance(corpus_case, str)
    case = Path("evaluation/development/multitest-open-corpus-v1/cases") / corpus_case
    csv_content = (case / "data.csv").read_bytes()
    rows = list(csv.reader(io.StringIO(csv_content.decode("utf-8"))))
    header = tuple(rows[0])
    counts = Counter(row[1] for row in rows[1:])

    def finite(value: str) -> bool:
        try:
            number = float(value)
        except ValueError:
            return False
        return number == number and number not in {float("inf"), float("-inf")}

    outcomes = tuple(
        column
        for index, column in enumerate(header)
        if index not in {0, 1} and all(finite(row[index]) for row in rows[1:])
    )
    return dataflow.analyze_code_csv_multiple_testing_dataflow(
        source.encode(),
        authorized_path="data.csv",
        group_column=header[1],
        outcome_columns=outcomes,
        csv_header=header,
        group_values=tuple(sorted(counts, key=lambda value: value.encode("utf-8"))),
        csv_content=csv_content,
    )


def _explicit(
    *,
    columns: tuple[str, ...] = ("m1", "m2", "m3"),
    decisions: str | None = None,
    imports: str = "",
    before: str = "",
    after: str = "",
    selection: str | None = None,
) -> str:
    calls: list[str] = []
    for index, column in enumerate(columns):
        left = f'df.loc[df["group"] == "a", "{column}"]'
        right = f'df.loc[df["group"] == "b", "{column}"]'
        if selection is not None:
            left = selection.format(group="a", column=column)
            right = selection.format(group="b", column=column)
        calls.append(f"r{index} = stats.ttest_ind({left}, {right})")
    if decisions is None:
        decisions = "\n".join(f"print(r{index}.pvalue < 0.05)" for index in range(len(columns)))
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{imports}"
        'df = pd.read_csv("data.csv")\n'
        f"{before}" + "\n".join(calls) + "\n" + decisions + "\n" + after
    )


def test_explicit_complete_family_without_correction_is_candidate_fact() -> None:
    result = _run(_explicit())

    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "none"
    assert result.facts.registered_test_api == "scipy.stats.ttest_ind"
    assert result.facts.family_size == 3
    assert result.facts.corrected_positions == ()
    assert result.facts.conclusion_positions == (0, 1, 2)


@pytest.mark.parametrize("shape", ["loop", "comprehension", "helper"])
def test_closed_family_battery_expansions_preserve_exact_n(shape: str) -> None:
    prelude = "import pandas as pd\nfrom scipy import stats\n"
    reader = 'df = pd.read_csv("data.csv")\n'
    conclusions = (
        "print(results[0].pvalue < 0.05)\n"
        "print(results[1].pvalue < 0.05)\n"
        "print(results[2].pvalue < 0.05)\n"
    )
    if shape == "loop":
        source = (
            prelude
            + reader
            + 'OUTCOMES = ["m1", "m2", "m3"]\nresults = []\n'
            + "for column in OUTCOMES:\n"
            + "    results.append(stats.ttest_ind("
            + 'df.loc[df["group"] == "a", column], '
            + 'df.loc[df["group"] == "b", column]))\n'
            + conclusions
        )
    elif shape == "comprehension":
        source = (
            prelude
            + reader
            + 'OUTCOMES = ["m1", "m2", "m3"]\n'
            + "results = [stats.ttest_ind("
            + 'df.loc[df["group"] == "a", column], '
            + 'df.loc[df["group"] == "b", column]) for column in OUTCOMES]\n'
            + conclusions
        )
    else:
        source = (
            prelude
            + "def test_one(frame, column):\n"
            + "    return stats.ttest_ind("
            + 'frame.loc[frame["group"] == "a", column], '
            + 'frame.loc[frame["group"] == "b", column])\n'
            + reader
            + 'r0 = test_one(df, "m1")\nr1 = test_one(df, "m2")\n'
            + 'r2 = test_one(df, "m3")\nresults = [r0, r1, r2]\n'
            + conclusions
        )
    result = _run(source)
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.family_size == 3


@pytest.mark.parametrize(
    "iterable",
    [
        '["m2", "m1", "m3"]',
        "sorted(OUTCOMES)",
        "set(OUTCOMES)",
        "make_outcomes()",
    ],
)
def test_only_order_equal_family_iterables_are_expandable(iterable: str) -> None:
    source = (
        "import pandas as pd\nfrom scipy import stats\n"
        'OUTCOMES = ["m1", "m2", "m3"]\n'
        "def make_outcomes():\n    return OUTCOMES\n"
        'df = pd.read_csv("data.csv")\nresults = []\n'
        f"for column in {iterable}:\n"
        "    results.append(stats.ttest_ind("
        'df.loc[df["group"] == "a", column], '
        'df.loc[df["group"] == "b", column]))\n'
        "print(results)\n"
    )
    assert _run(source).reason == "test-battery-cardinality-unresolved"


def test_default_method_multipletests_is_a_covered_negative() -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        "reject, adjusted, _, _ = multipletests(pvalues)\n"
        "print(reject[0])\nprint(reject[1])\nprint(reject[2])"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        )
    )

    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"
    assert result.facts.correction_methods == ("hs",)


@pytest.mark.parametrize("method", sorted(dataflow._MT_MULTIPLETESTS_METHODS))
def test_every_registered_multipletests_method_covers_inputs_by_value(method: str) -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        f'reject, adjusted, _, _ = multipletests(pvalues, method="{method}")\n'
        "print(reject[0])\nprint(reject[1])\nprint(reject[2])"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        )
    )
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"
    assert result.facts.correction_methods == (method,)


@pytest.mark.parametrize("method", ["indep", "negcorr"])
def test_fdrcorrection_registered_methods_cover_complete_inputs(method: str) -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        f'reject, adjusted = fdrcorrection(pvalues, method="{method}")\n'
        "print(reject[0])\nprint(reject[1])\nprint(reject[2])"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import fdrcorrection\n",
            decisions=decisions,
        )
    )
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"


@pytest.mark.parametrize("axis", ["", ", axis=0", ", axis=-1", ", axis=None"])
@pytest.mark.parametrize("method", ["bh", "by"])
def test_false_discovery_control_closed_axis_and_method_grammar(axis: str, method: str) -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        f'adjusted = false_discovery_control(pvalues, method="{method}"{axis})\n'
        "print(adjusted[0] < 0.05)\n"
        "print(adjusted[1] < 0.05)\n"
        "print(adjusted[2] < 0.05)"
    )
    result = _run(
        _explicit(
            imports="from scipy.stats import false_discovery_control\n",
            decisions=decisions,
        )
    )
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"


@pytest.mark.parametrize("axis", [", axis=1", ", axis=AXIS", ", axis=0 + 0"])
def test_false_discovery_control_refuses_every_other_axis(axis: str) -> None:
    source = "AXIS = 0\n" + _explicit(
        imports="from scipy.stats import false_discovery_control\n",
        decisions=(
            "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
            f"adjusted = false_discovery_control(pvalues{axis})\n"
            "print(adjusted[0] < 0.05)\n"
            "print(adjusted[1] < 0.05)\n"
            "print(adjusted[2] < 0.05)"
        ),
    )
    assert _run(source).reason == "correction-family-lineage-unresolved"


def test_registered_strict_subset_correction_retains_excluded_raw_member() -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue]\n"
        "reject, adjusted, _, _ = multipletests(pvalues)\n"
        "print(reject[0])\nprint(reject[1])\nprint(r2.pvalue < 0.05)"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        )
    )
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "strict_subset"
    assert result.facts.corrected_positions == (0, 1)


@pytest.mark.parametrize(
    ("container", "expected"),
    [
        ("slice", "strict_subset"),
        ("concatenation", "complete"),
        ("zip-direct", "correction-family-lineage-unresolved"),
        ("zip-p-field-comprehension", "complete"),
    ],
)
def test_v2_p_container_reconstruction_grammar(container: str, expected: str) -> None:
    columns = ("m1", "m2", "m3", "m4")
    if container == "slice":
        decisions = (
            "pvals = [r0.pvalue, r1.pvalue, r2.pvalue, r3.pvalue]\n"
            "reject, adjusted, _, _ = multipletests(pvals[:3])\n"
            "print(reject[0]); print(reject[1]); print(reject[2]); print(r3.pvalue < 0.05)"
        )
    elif container == "concatenation":
        decisions = (
            "pvals = [r0.pvalue, r1.pvalue]\nextra = [r2.pvalue, r3.pvalue]\n"
            "reject, adjusted, _, _ = multipletests(pvals + extra)\n"
            "print(reject[0]); print(reject[1]); print(reject[2]); print(reject[3])"
        )
    elif container == "zip-direct":
        decisions = (
            'OUTCOMES = ["m1", "m2", "m3", "m4"]\n'
            "pvals = [r0.pvalue, r1.pvalue, r2.pvalue, r3.pvalue]\n"
            "reject, adjusted, _, _ = multipletests(zip(OUTCOMES, pvals))\n"
            "print(reject[0]); print(reject[1]); print(reject[2]); print(reject[3])"
        )
    else:
        decisions = (
            'OUTCOMES = ["m1", "m2", "m3", "m4"]\n'
            "pvals = [r0.pvalue, r1.pvalue, r2.pvalue, r3.pvalue]\n"
            "selected = [p for name, p in zip(OUTCOMES, pvals)]\n"
            "reject, adjusted, _, _ = multipletests(selected)\n"
            "print(reject[0]); print(reject[1]); print(reject[2]); print(reject[3])"
        )
    result = _run(
        _explicit(
            columns=columns,
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        ),
        columns,
    )
    if expected == "correction-family-lineage-unresolved":
        assert result.reason == expected
        assert result.facts is None
    else:
        assert result.reason is None
        assert result.facts is not None
        assert result.facts.correction_classification == expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        pytest.param("[r0.pvalue, r1.pvalue]", "(r2.pvalue,)", None, id="J1-list-tuple"),
        pytest.param("(r0.pvalue, r1.pvalue)", "[r2.pvalue]", None, id="J2-tuple-list"),
        pytest.param(
            "[r0.pvalue, r1.pvalue]",
            "[r2.pvalue]",
            "strict_subset",
            id="same-kind-list-control",
        ),
    ],
)
def test_pseq_concatenation_requires_matching_container_kinds(
    left: str, right: str, expected: str | None
) -> None:
    columns = ("m1", "m2", "m3", "m4")
    decisions = (
        f"pvals = {left}\nextra = {right}\n"
        "reject, adjusted, _, _ = multipletests(pvals + extra)\n"
        "print(reject[0]); print(reject[1]); print(reject[2]); print(r3.pvalue < 0.05)"
    )
    result = _run(
        _explicit(
            columns=columns,
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        ),
        columns,
    )
    if expected is None:
        assert result.reason == "correction-family-lineage-unresolved"
        assert result.facts is None
    else:
        assert result.reason is None
        assert result.facts is not None
        assert result.facts.correction_classification == expected


def test_two_disjoint_registered_correction_families_abstain_as_partitioned() -> None:
    decisions = (
        "first = [r0.pvalue]\nsecond = [r1.pvalue, r2.pvalue]\n"
        "reject_first, _, _, _ = multipletests(first)\n"
        "reject_second, _, _, _ = multipletests(second)\n"
        "print(reject_first[0])\nprint(reject_second[0])\nprint(reject_second[1])"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        )
    )
    assert result.reason == "multiple-family-partition-present"


def test_exact_manual_bonferroni_adjusted_values_cover_complete_family() -> None:
    decisions = (
        "N = 3\n"
        "a0 = min(r0.pvalue * N, 1)\n"
        "a1 = min(N * r1.pvalue, 1)\n"
        "a2 = numpy.minimum(r2.pvalue * 3, 1)\n"
        "print(a0 < 0.05)\nprint(a1 < 0.05)\nprint(a2 < 0.05)"
    )
    result = _run(_explicit(imports="import numpy\n", decisions=decisions))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"
    assert result.facts.correction_methods == ("bonferroni",)


def test_adjusted_correction_return_is_covered_from_input_membership() -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        "reject, adjusted, _, _ = multipletests(pvalues)\n"
        "print(adjusted[0] < 0.05)\n"
        "print(adjusted[1] < 0.05)\n"
        "print(adjusted[2] < 0.05)"
    )
    result = _run(
        _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=decisions,
        )
    )
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "complete"


@pytest.mark.parametrize("operator", ["<", "<=", ">", ">="])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("alpha", ["0.01", "0.05", "0.1"])
def test_all_direct_p_comparison_forms_are_closed(operator: str, reverse: bool, alpha: str) -> None:
    columns = ("m1", "m2", "m3", "m4")
    expressions = []
    for index in range(len(columns)):
        left, right = f"r{index}.pvalue", alpha
        if reverse:
            left, right = right, left
        expressions.append(f"print({left} {operator} {right})")
    result = _run(_explicit(columns=columns, decisions="\n".join(expressions)), columns)

    if alpha == "0.05":
        assert result.reason is None
        assert result.facts is not None
    else:
        assert result.reason == "unresolved-decision-threshold"
        assert result.facts is None


def test_correct_bare_literal_bonferroni_off_ast_stops_at_order_15() -> None:
    columns = ("m1", "m2", "m3", "m4", "m5")
    source = _explicit(
        columns=columns,
        decisions="\n".join(f"print(r{index}.pvalue < 0.01)" for index in range(len(columns))),
    )

    assert _run(source, columns).reason == "unresolved-decision-threshold"


@pytest.mark.parametrize("literal", ["0.0100000000000000001", "0.0099999999999999999"])
def test_decimal_product_rule_uses_literal_source_text_not_binary_float(literal: str) -> None:
    import ast
    from decimal import Decimal

    node = ast.parse(literal, mode="eval").body
    assert dataflow._mt_decimal_literal(node, literal) == Decimal(literal)
    assert dataflow._mt_decimal_literal(node, literal) != Decimal(float(literal))


@pytest.mark.parametrize(
    ("threshold", "expected"),
    [
        ("0.05 / 3", "unresolved-decision-threshold"),
        ("1 - (1 - 0.05) ** (1 / 3)", "unresolved-decision-threshold"),
        ("ALPHA", None),
        ("thresholds[0]", "unresolved-decision-threshold"),
        ("make_threshold()", "unresolved-decision-threshold"),
    ],
)
def test_computed_or_unresolved_thresholds_abstain(threshold: str, expected: str | None) -> None:
    setup = "ALPHA = 0.05\nthresholds = [0.05]\ndef make_threshold():\n    return 0.05\n"
    decisions = "\n".join(f"print(r{i}.pvalue < {threshold})" for i in range(3))
    assert _run(setup + _explicit(decisions=decisions)).reason == expected


def test_unclamped_manual_bonferroni_transform_never_classifies_none() -> None:
    source = _explicit(
        decisions=(
            "a0 = r0.pvalue * 3\na1 = r1.pvalue * 3\na2 = r2.pvalue * 3\n"
            "print(a0 < 0.05)\nprint(a1 < 0.05)\nprint(a2 < 0.05)"
        )
    )
    assert _run(source).reason == "unresolved-manual-correction-present"


@pytest.mark.parametrize(
    "terminal",
    [
        "multipletests",
        "fdrcorrection",
        "false_discovery_control",
        "multicomp",
        "fdr_correction",
        "p_adjust",
        "padjust",
        "bonferroni",
        "holm",
        "sidak",
        "benjamini_hochberg",
    ],
)
def test_module_independent_callee_terminal_census(terminal: str) -> None:
    source = _explicit(after=f"opaque.{terminal}([1, 2, 3])\n")
    assert _run(source).reason == "unresolved-manual-correction-present"


@pytest.mark.parametrize("identifier", ["bonferroni", "holm", "sidak", "benjamini_hochberg"])
def test_non_callee_identifier_spellings_do_not_enter_correction_census(identifier: str) -> None:
    source = _explicit(before=f"{identifier} = 7\n", after=f"print({identifier})\n")
    assert _run(source).reason is None


def test_off_registry_correction_is_guarded_by_terminal_slot() -> None:
    source = _explicit(
        imports="import pingouin\n",
        after="pingouin.multicomp([r0.pvalue, r1.pvalue, r2.pvalue])\n",
    )
    assert _run(source).reason == "unresolved-manual-correction-present"


def test_cross_module_numpy_correction_helper_is_an_opaque_pvalue_consumer() -> None:
    source = _explicit(
        imports="from external_adjustment import adjust_values\n",
        after="adjust_values([r0.pvalue, r1.pvalue, r2.pvalue])\n",
    )
    assert _run(source).reason == "unresolved-pvalue-consumer"


def test_loaded_adjusted_pvalue_conclusions_do_not_acquire_local_p_lineage() -> None:
    after = (
        'adjusted = numpy.load("adjusted.npy")\n'
        "print(adjusted[0] < 0.05)\n"
        "print(adjusted[1] < 0.05)\n"
        "print(adjusted[2] < 0.05)\n"
    )
    assert (
        _run(_explicit(imports="import numpy\n", after=after)).reason
        == "upstream-correction-lineage-unresolved"
    )


def test_dynamic_family_member_index_abstains_at_order_12() -> None:
    decisions = (
        "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
        "member = 0\n"
        "print(pvalues[member] < 0.05)\n"
        "print(r1.pvalue < 0.05)\n"
        "print(r2.pvalue < 0.05)"
    )
    assert _run(_explicit(decisions=decisions)).reason == ("pvalue-family-collection-unresolved")


def test_unordered_family_pvalue_set_abstains_at_order_12() -> None:
    source = _explicit(after="unordered = {r0.pvalue, r1.pvalue, r2.pvalue}\n")
    assert _run(source).reason == "pvalue-family-collection-unresolved"


def test_sensitivity_duplicate_stops_before_operand_resolution() -> None:
    source = _explicit(
        before=(
            'unused = stats.ttest_ind(df.loc[df["group"] == "a", "missing"], '
            'df.loc[df["group"] == "b", "missing"])\n'
        )
    )
    assert _run(source).reason == "extra-registered-test-outside-authorized-family"


def test_global_censuses_do_not_override_ordered_first_reason_selection() -> None:
    source = _explicit(
        before=(
            'unused = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        after="opaque.holm([r0.pvalue, r1.pvalue, r2.pvalue])\n",
    )
    assert _run(source).reason == "extra-registered-test-outside-authorized-family"


def test_literal_false_family_call_never_becomes_an_established_instance() -> None:
    source = _explicit(
        before=(
            "if False:\n"
            '    dead = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        )
    )
    assert _run(source).reason == "test-battery-cardinality-unresolved"


def test_family_call_under_live_if_stops_at_incomplete_census() -> None:
    source = _explicit(
        before=(
            "if True:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        )
    )
    assert _run(source).reason == "authorized-family-test-census-incomplete"


def test_family_call_in_except_handler_stops_at_incomplete_census() -> None:
    source = _explicit(
        before=(
            "try:\n"
            "    pass\n"
            "except ValueError:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        )
    )
    assert _run(source).reason == "authorized-family-test-census-incomplete"


@pytest.mark.parametrize(
    "before",
    [
        (
            "condition = True\n"
            "if condition:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "if True:\n"
            "    pass\n"
            "elif False:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "if True:\n"
            "    if True:\n"
            '        conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "while True:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "try:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
            "except ValueError:\n"
            "    pass\n"
        ),
        (
            "try:\n"
            "    pass\n"
            "except ValueError:\n"
            "    pass\n"
            "else:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "try:\n"
            "    pass\n"
            "finally:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "from contextlib import suppress\n"
            "with suppress(ValueError):\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
        (
            "match 1:\n"
            "    case 1:\n"
            '        conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        ),
    ],
)
def test_every_other_conditional_family_call_stops_at_incomplete_census(before: str) -> None:
    assert _run(_explicit(before=before)).reason == "authorized-family-test-census-incomplete"


def test_literal_false_while_family_call_stops_at_unresolved_cardinality() -> None:
    source = _explicit(
        before=(
            "while False:\n"
            '    dead = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n'
        )
    )
    assert _run(source).reason == "test-battery-cardinality-unresolved"


def test_discovery_validation_split_abstains_on_row_completeness() -> None:
    selection = 'df.loc[(df["group"] == "{group}") & (df["{column}"] > 0), "{column}"]'
    assert _run(_explicit(selection=selection)).reason == "selected-group-row-completeness-unproven"


def test_exact_literal_query_is_the_only_additional_row_mask_exemption() -> None:
    selection = 'df.query("group == \'{group}\'")["{column}"]'
    assert _run(_explicit(selection=selection)).reason is None


def test_boolean_mask_subscript_is_never_query_exempt() -> None:
    selection = 'df[df["group"] == "{group}"]["{column}"]'
    assert _run(_explicit(selection=selection)).reason is None


def test_numpy_omnibus_assert_gate_abstains() -> None:
    before = (
        'gate = numpy.abs(numpy.mean(df.loc[df["group"] == "a", ["m1", "m2", "m3"]]'
        '.to_numpy(), axis=0) - numpy.mean(df.loc[df["group"] == "b", '
        '["m1", "m2", "m3"]].to_numpy(), axis=0)).sum()\n'
        "assert gate > 0\n"
    )
    source = _explicit(imports="import numpy\n", before=before)
    assert _run(source).reason == "hierarchical-gatekeeping-present"


def test_match_subject_and_guard_are_hierarchical_control_edges() -> None:
    before = (
        'gate = df[["m1", "m2", "m3"]].to_numpy().sum()\n'
        "match gate:\n"
        "    case value if value > 0:\n"
        "        ready = True\n"
        "    case _:\n"
        "        ready = False\n"
    )
    assert _run(_explicit(before=before)).reason == "hierarchical-gatekeeping-present"


def test_boolean_short_circuit_feeding_assert_is_hierarchical_control() -> None:
    before = (
        'gate = df[["m1", "m2", "m3"]].to_numpy().sum()\n'
        "ready = True\n"
        "combined = ready and gate > 0\n"
        "assert combined\n"
    )
    assert _run(_explicit(before=before)).reason == "hierarchical-gatekeeping-present"


def test_constant_string_terminal_rendering_is_total_and_presentation_only() -> None:
    decisions = (
        's0 = "yes" if r0.pvalue < 0.05 else "no"\n'
        's1 = "yes" if r1.pvalue < 0.05 else "no"\n'
        's2 = "yes" if r2.pvalue < 0.05 else "no"\n'
        "print(s0); print(s0); print(s1); print(s2)"
    )
    result = _run(_explicit(decisions=decisions))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.correction_classification == "none"


@pytest.mark.parametrize(
    "decisions",
    [
        (
            's0 = "yes" if r0.pvalue < 0.05 else "no"\n'
            's1 = "yes" if r1.pvalue < 0.05 else "no"\n'
            's2 = "yes" if r2.pvalue < 0.05 else "no"\n'
            "print(s0); print(s1); print(s2); consume(s0)"
        ),
        (
            's0 = "yes" if r0.pvalue < 0.05 else "no"\n'
            's1 = "yes" if r1.pvalue < 0.05 else "no"\n'
            's2 = "yes" if r2.pvalue < 0.05 else "no"\n'
            "if READY:\n    print(s0)\nprint(s1); print(s2)"
        ),
        (
            's0 = "yes".upper() if r0.pvalue < 0.05 else "no"\n'
            's1 = "yes" if r1.pvalue < 0.05 else "no"\n'
            's2 = "yes" if r2.pvalue < 0.05 else "no"\n'
            "print(s0); print(s1); print(s2)"
        ),
    ],
)
def test_every_nonterminal_rendering_consumer_returns_to_hierarchy(decisions: str) -> None:
    source = "READY = True\ndef consume(value):\n    return value\n" + _explicit(
        decisions=decisions
    )
    assert _run(source).reason == "hierarchical-gatekeeping-present"


def test_unresolved_execution_prevention_residual_has_distinct_reason() -> None:
    after = (
        "ready = True\n"
        "try:\n"
        '    diagnostic = numpy.mean(df[["m1", "m2", "m3"]].to_numpy())\n'
        "finally:\n"
        "    assert ready\n"
    )
    assert (
        _run(_explicit(imports="import numpy\n", after=after)).reason
        == "pvalue-control-dependence-unresolved"
    )


@pytest.mark.parametrize(
    ("after", "reason"),
    [
        (
            "pvalues = pd.Series([r0.pvalue, r1.pvalue, r2.pvalue])\n"
            'pvalues.to_csv("pvalues.csv")\n',
            "unresolved-pvalue-consumer",
        ),
        (
            'pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\nnumpy.savetxt("pvalues.csv", pvalues)\n',
            "unresolved-pvalue-consumer",
        ),
        (
            "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
            'json.dump(pvalues, open("pvalues.json", "w"))\n',
            "unresolved-pvalue-consumer",
        ),
    ],
)
def test_guard_terminal_exports_abstain(after: str, reason: str) -> None:
    imports = "import numpy\nimport json\n" if "numpy" in after or "json" in after else ""
    assert _run(_explicit(imports=imports, after=after)).reason == reason


@pytest.mark.parametrize(
    "summary",
    [
        "min(pvalues)",
        "max(pvalues)",
        "numpy.nanmin(pvalues)",
        "numpy.nanmax(pvalues)",
        "pd.Series(pvalues).min()",
        "pd.Series(pvalues).max()",
        "sorted(pvalues)[0]",
        "sorted(pvalues)[-1]",
    ],
)
def test_exact_family_extremum_registry(summary: str) -> None:
    after = f"pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\nprint({summary})\n"
    assert (
        _run(_explicit(imports="import numpy\n", after=after)).reason
        == "family-pvalue-extremum-reduction-present"
    )


@pytest.mark.parametrize(
    "summary",
    [
        "numpy.argmin(pvalues)",
        "pd.Series(pvalues).idxmin()",
        "numpy.partition(pvalues, 0)[0]",
        "heapq.nsmallest(1, pvalues)[0]",
    ],
)
def test_unregistered_extremum_shapes_abstain_as_manual_correction(summary: str) -> None:
    after = f"pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\nprint({summary})\n"
    assert (
        _run(_explicit(imports="import numpy\nimport heapq\n", after=after)).reason
        == "unresolved-manual-correction-present"
    )


def test_numeric_pvalue_table_only_has_no_memberwise_conclusions() -> None:
    result = _run(_explicit(decisions="print(r0.pvalue)\nprint(r1.pvalue)\nprint(r2.pvalue)"))
    assert result.reason == "pderived-conclusion-family-incomplete"


def test_dynamic_resampling_cardinality_has_its_own_first_reason() -> None:
    after = (
        "null = []\n"
        "for _ in range(20 * len(df)):\n"
        "    permuted = df.sample(frac=1)\n"
        '    null.append(max(permuted["m1"]))\n'
    )
    assert _run(_explicit(after=after)).reason == "resampling-cardinality-unresolved"


def test_resolved_label_permutation_max_t_abstains() -> None:
    after = (
        "null = []\n"
        "for _ in range(20):\n"
        "    permuted = df.sample(frac=1)\n"
        '    null.append(max(permuted["m1"]))\n'
    )
    assert _run(_explicit(after=after)).reason == "permutation-family-control-present"


def test_statistics_prefix_sibling_abstains() -> None:
    assert (
        _run(_explicit(after='print(stats.shapiro(df["m1"]))\n')).reason
        == "unresolved-inference-sibling-present"
    )


def test_sem_exemption_is_limited_to_output_identity_arithmetic_and_formatting() -> None:
    source = _explicit(
        after=(
            'uncertainty = stats.sem(df["m1"], ddof=1)\nprint(f"uncertainty={uncertainty + 1}")\n'
        )
    )
    assert _run(source).reason is None


@pytest.mark.parametrize(
    ("consumer", "reason"),
    [
        ("print(uncertainty < 0.05)", "unresolved-inference-sibling-present"),
        ("print([uncertainty])", "unresolved-inference-sibling-present"),
        ("assert uncertainty", "unresolved-inference-sibling-present"),
        ("if uncertainty:\n    print('selected')", "unresolved-inference-sibling-present"),
    ],
)
def test_sem_exemption_refuses_decision_container_and_control_consumers(
    consumer: str, reason: str
) -> None:
    source = _explicit(
        after=f'uncertainty = stats.sem(df["m1"])\n{consumer}\n',
    )
    assert _run(source).reason == reason


@pytest.mark.parametrize(
    "expression",
    [
        "stats.t.ppf(0.9, len(df) - 2)",
        'stats.t.ppf(0.95, df["m1"].var())',
        'stats.t.ppf(0.975, len(["x", "y", "z"]) + 30)',
        "stats.t.ppf(0.99, len(df) - 2)",
        "stats.t.ppf(0.995, len(df) - 2)",
        "stats.t.ppf(1 - 0.05 / 3, len(df) - 2)",
    ],
)
def test_every_t_ppf_shape_takes_normal_statistics_prefix_abstention(expression: str) -> None:
    source = _explicit(after=f"print({expression})\n")
    assert _run(source).reason == "unresolved-inference-sibling-present"


def test_prose_tripwire_and_promoted_non_callee_renames_preserve_first_result() -> None:
    baseline = _run(_explicit())
    variants = [
        "# bonferroni holm sidak benjamini_hochberg\n" + _explicit(),
        '"""primary/exploratory score correction prose"""\n' + _explicit(),
        _explicit(after='print("multipletests correction primary score")\n'),
    ]
    for name in ("bonferroni", "holm", "sidak", "benjamini_hochberg"):
        variants.append(_explicit(before=f"{name} = 4\n", after=f"print({name})\n"))
    assert baseline.reason is None
    for source in variants:
        result = _run(source)
        assert result.reason == baseline.reason
        assert result.facts is not None and baseline.facts is not None
        assert result.facts.correction_classification == baseline.facts.correction_classification
        assert result.facts.corrected_positions == baseline.facts.corrected_positions
        assert result.facts.conclusion_positions == baseline.facts.conclusion_positions


def test_every_isolated_guard_fixture_is_prose_mutation_invariant() -> None:
    namespace = runpy.run_path(
        "evaluation/development/multitest-code-slice-v2_1/ADVERSARY_FIXTURES.py"
    )
    fixtures = namespace["FIXTURES"]
    for fixture in fixtures.values():
        source = fixture["source"]
        columns = fixture.get("columns", ("m1", "m2", "m3"))
        baseline = _run(source, columns)
        variants = [
            '"""Unrelated module documentation."""\n' + source,
            source + "\n# Unrelated trailing source comment.\n",
            source + '\nunrelated_label = "human-readable report label"\n',
            source.replace("print(", 'print("output label", '),
            source + '\nprint(f"human-readable format text")\n',
            source + '\nunrelated_annotation: str = "display-only annotation"\n',
        ]
        if "benjamini_hochberg =" not in source:
            variants.append(
                source + "\nbonferroni = 1\nholm = 2\nsidak = 3\n" + "benjamini_hochberg = 4\n"
            )
        for variant in variants:
            result = _run(variant, columns)
            assert result.reason == baseline.reason
            assert (result.facts is None) == (baseline.facts is None)
            if result.facts is not None and baseline.facts is not None:
                assert result.facts.correction_classification == (
                    baseline.facts.correction_classification
                )
                assert result.facts.corrected_positions == baseline.facts.corrected_positions
                assert result.facts.conclusion_positions == baseline.facts.conclusion_positions


@pytest.mark.parametrize(
    ("before", "expected"),
    [
        (
            "if False:\n"
            '    dead = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n',
            "test-battery-cardinality-unresolved",
        ),
        (
            "if True:\n"
            '    conditional = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
            'df.loc[df["group"] == "b", "m1"])\n',
            "authorized-family-test-census-incomplete",
        ),
    ],
)
def test_conditional_census_predicates_are_prose_mutation_invariant(
    before: str, expected: str
) -> None:
    source = _explicit(before=before)
    variants = (
        '"""Unrelated conditional-analysis description."""\n' + source,
        source + "\n# Unrelated report text.\n",
        source + '\nreport_label = "if False means sensitivity only"\n',
    )
    assert _run(source).reason == expected
    assert all(_run(variant).reason == expected for variant in variants)


def test_structural_literal_deletion_is_a_tripwire_positive_control() -> None:
    baseline = _run(_explicit())
    mutated = _explicit().replace('"m3"', '"missing"', 1)
    assert baseline.reason is None
    assert _run(mutated).reason == "test-operand-lineage-unresolved"


def test_non_callee_rename_has_paired_callee_terminal_control() -> None:
    renamed = _explicit(before="bonferroni = 4\n", after="print(bonferroni)\n")
    called = _explicit(
        imports="from external_adjustment import bonferroni\n",
        after="bonferroni([r0.pvalue, r1.pvalue, r2.pvalue])\n",
    )
    assert _run(renamed).reason is None
    assert _run(called).reason == "unresolved-manual-correction-present"


def test_v2_integrity_and_control_registries_are_exact() -> None:
    assert dataflow._MT_V2_DYNAMIC_EXECUTION_REGISTRY == (
        "exec",
        "eval",
        "compile",
        "__import__",
        "importlib.import_module",
        "getattr(imported-module)",
        "setattr(imported-module)",
        "globals-mutation",
        "locals-mutation",
    )
    assert dataflow._MT_V2_API_REBINDING_REGISTRY == (
        "registered-or-statistics-module-attribute-store-or-del",
        "live-api-alias-function-definition",
        "live-api-alias-async-function-definition",
        "live-api-alias-class-definition",
        "live-api-alias-argument-binding",
        "live-api-alias-name-store-or-del",
    )
    assert dataflow._MT_V2_CONTROL_NODE_REGISTRY == (
        "registered-test-call-argument",
        "recognized-correction-call-argument",
        "p-derived-conclusion-operand",
        "family-container-control-insertion",
        "If.test",
        "IfExp.test",
        "While.test",
        "Assert.test",
        "Match.subject",
        "match_case.guard",
        "For.iter",
        "AsyncFor.iter",
        "comprehension.iter",
        "comprehension.if",
        "BoolOp.short-circuit-operand",
        "registered-sink-member-selector",
        "return",
        "break",
        "continue",
        "raise",
        "sys.exit",
        "execution-prevention-residual",
    )


@pytest.mark.parametrize(
    ("imports", "statement"),
    [
        ("", 'exec("pass")'),
        ("", 'eval("1")'),
        ("", 'compile("1", "<x>", "eval")'),
        ("", '__import__("math")'),
        ("import importlib\n", 'importlib.import_module("math")'),
        ("", 'getattr(pd, "read_csv")'),
        ("", 'setattr(pd, "read_csv", object())'),
        ("", 'globals()["hidden"] = 1'),
        ("", 'scope = locals()\nscope.update({"hidden": 1})'),
    ],
)
def test_dynamic_execution_census_is_whole_module(imports: str, statement: str) -> None:
    source = _explicit(
        imports=imports,
        after=f"def unused():\n    {statement.replace(chr(10), chr(10) + '    ')}\n",
    )
    assert _run(source).reason == "api-resolution-ambiguous"


@pytest.mark.parametrize(
    "statement",
    [
        "stats.ttest_ind = object()",
        "stats = object()",
        "def stats():\n    return None",
        "class stats:\n    pass",
        "def unused(stats):\n    return stats",
    ],
)
def test_live_api_rebinding_census_is_whole_module(statement: str) -> None:
    assert _run(_explicit(after=statement + "\n")).reason == "api-resolution-ambiguous"


def test_same_terminal_spelling_without_a_live_alias_does_not_rebind_an_api() -> None:
    source = _explicit(before="ttest_ind = 4\n", after="print(ttest_ind)\n")
    assert _run(source).reason is None


@pytest.mark.parametrize(
    "exit_body",
    [
        "if gate > 0:\n    return",
        "for _ in range(1):\n    if gate > 0:\n        break",
        "for _ in range(1):\n    if gate > 0:\n        continue",
        'if gate > 0:\n    raise RuntimeError("panel gate")',
        "if gate > 0:\n    sys.exit(0)",
    ],
)
def test_every_early_exit_kind_preserves_hierarchy(exit_body: str) -> None:
    imports = "import sys\nimport numpy\n" if "sys.exit" in exit_body else "import numpy\n"
    source = _explicit(
        imports=imports,
        before=('gate = numpy.sum(df[["m1", "m2", "m3"]].to_numpy())\n' + exit_body + "\n"),
    )
    assert _run(source).reason == "hierarchical-gatekeeping-present"


def test_mixed_integrity_projection_does_not_become_joint_scientific_control() -> None:
    source = _explicit(
        before=(
            'required = ["batch_id", "group", "m1", "m2", "m3"]\n'
            "if df[required].isna().any().any():\n"
            '    raise ValueError("invalid data")\n'
        )
    )
    assert _run(source).reason is None


def test_unresolved_pvalue_attribute_store_never_crosses_forward_slice() -> None:
    source = _explicit(after="holder = type('Holder', (), {})()\nholder.value = r0.pvalue\n")
    assert _run(source).reason == "unresolved-pvalue-consumer"


@pytest.mark.parametrize(
    ("consumer", "reason"),
    [
        ('mapping = {r0.pvalue: "member"}', "pvalue-family-collection-unresolved"),
        ("selected = values[r0.pvalue]", "unresolved-pvalue-consumer"),
        ("component = r0.pvalue.real", "unresolved-pvalue-consumer"),
        ('opaque(f"p={r0.pvalue}")', "unresolved-pvalue-consumer"),
    ],
)
def test_forward_slice_accounts_for_structural_p_consumers(consumer: str, reason: str) -> None:
    source = _explicit(
        before="values = [1, 2, 3]\n",
        after="def opaque(value):\n    return value\n" + consumer + "\n",
    )
    assert _run(source).reason == reason


def test_statistics_prefix_registry_is_byte_equal_to_qualified_v3_1() -> None:
    source = __import__(
        "sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1",
        fromlist=["_STATISTICS_PREFIXES"],
    )._STATISTICS_PREFIXES
    assert dataflow._STATISTICS_PREFIXES == source


def test_every_inherited_mt_registry_is_byte_equal_to_v1_1() -> None:
    frozen = __import__(
        "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1_1",
        fromlist=["_MT_TEST_APIS"],
    )
    for name in (
        "_MT_TEST_APIS",
        "_MT_CORRECTION_APIS",
        "_MT_MULTIPLETESTS_METHODS",
        "_MT_DECISION_LITERALS",
        "_MT_CORRECTION_TERMINALS",
        "_MT_UNRECOGNIZED_EXTREMUM_TERMINALS",
        "_V2_RANDOM_MODULE_DRAWS",
        "_V2_RANDOM_GENERATOR_METHODS",
    ):
        assert getattr(dataflow, name) == getattr(frozen, name)


def test_position_one_projection_is_pinned_to_the_two_locked_scipy_versions() -> None:
    lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
    assert {package["version"] for package in lock["package"] if package["name"] == "scipy"} == {
        "1.17.1",
        "1.18.0",
    }


def test_query_grammar_is_byte_equal_to_qualified_v3_1() -> None:
    qualified = __import__(
        "sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1",
        fromlist=["_QUERY"],
    )._QUERY
    assert (dataflow._MT_QUERY.pattern, dataflow._MT_QUERY.flags) == (
        qualified.pattern,
        qualified.flags,
    )
    assert re.fullmatch(dataflow._MT_QUERY, "group == 'a'") is not None


def test_opened_corpus_census_is_deterministic_and_has_no_candidate_shaped_three_call_api() -> None:
    roots = [Path("evaluation/development/blind-envelope-2026-08-21/cases")]
    roots.extend(
        Path(
            f"evaluation/development/blind-envelope-{envelope}-2026-08-"
            f"{'23' if envelope >= 7 else '22'}/cases"
        )
        for envelope in range(2, 10)
    )
    paths = sorted(path for root in roots for path in root.glob("*/project/analysis.py"))
    counts: list[tuple[str, ...]] = []
    terminal_slots: list[str] = []
    for path in paths:
        tree = dataflow._bounded_parse(path.read_bytes())
        scope = tuple(item for item in tree.body if not dataflow._is_docstring(item))
        resolver, reason = dataflow._resolver(scope)
        assert reason is None and resolver is not None
        apis = tuple(
            api
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (api := resolver.qualified(node.func)) in dataflow._MT_TEST_APIS
        )
        if len(apis) >= 2:
            counts.append(apis)
        terminal_slots.extend(
            terminal
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (terminal := (dataflow._mt_callee_terminal(node.func) or "").lower())
            and (terminal in dataflow._MT_CORRECTION_TERMINALS or terminal.startswith("benjamini"))
        )

    assert len(paths) == 98
    assert len(counts) == 19
    assert sum(len(items) == 2 for items in counts) == 12
    assert sum(len(items) == 3 for items in counts) == 7
    assert all(len(items) <= 3 for items in counts)
    assert all(
        items.count("scipy.stats.ttest_ind") == 2 and items.count("scipy.stats.mannwhitneyu") == 1
        for items in counts
        if len(items) == 3
    )
    assert (
        sum(
            set(items) == {"scipy.stats.ttest_ind", "scipy.stats.mannwhitneyu"}
            for items in counts
            if len(items) == 2
        )
        == 2
    )
    assert terminal_slots == []


def test_historical_answer_visible_guard_fixture_corpus_is_byte_untouched() -> None:
    root = Path("evaluation/development/multitest-code-slice-v1")
    payload = (root / "DEVELOPMENT_LEDGER.json").read_bytes()
    ledger = json.loads(payload)
    assert canonical_json(ledger).encode() == payload.rstrip(b"\n")
    namespace = runpy.run_path(str(root / "GUARD_FIXTURES.py"))
    assert ledger["fixture_count"] == len(namespace["FIXTURES"]) == 17


def test_v2_2_adversarial_guard_matrix_executes_with_exact_first_reasons() -> None:
    root = Path("evaluation/development/multitest-code-slice-v2_1")
    payload = (root / "DEVELOPMENT_LEDGER.json").read_bytes()
    ledger = json.loads(payload)
    assert canonical_json(ledger).encode() == payload.rstrip(b"\n")
    fixtures = runpy.run_path(str(root / "ADVERSARY_FIXTURES.py"))["FIXTURES"]
    assert ledger["fixture_count"] == len(fixtures) == 54
    assert [item["name"] for item in ledger["fixtures"]] == list(fixtures)
    for record in ledger["fixtures"]:
        fixture = fixtures[record["name"]]
        source = fixture["source"]
        assert record["source_sha256"] == dataflow.sha256_digest(source)
        result = _run_fixture(fixture)
        outcome = (
            "covered-negative"
            if result.facts is not None and result.facts.correction_classification == "complete"
            else "candidate"
            if result.facts is not None
            else result.reason
        )
        assert fixture["expected"] == record["expected"] == outcome


def test_frozen_v2_implementation_and_corpus_replay_anchors_are_explicit() -> None:
    anchors = {
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2.py": (
            "sha256:5f25aeab3e6c600794275918f9affcd19c33f877f770a6e3d7665fe8c33d5883"
        ),
        "src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2.py": (
            "sha256:8441c22502197d09855cbe0dac891bc7ba027185b8745aac9a4c708f28d738f6"
        ),
        "src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2.py": (
            "sha256:ba2507973937f1a95b800df48823c43c17d3a7b89df6ebc8892c8e675f6217b5"
        ),
        "src/sc_referee/scientific_checks/integration_multiple_testing_v2.py": (
            "sha256:508222f2a55345cd8f6c911fe7367f240e21c580300390bdc13e3ef8e8b02550"
        ),
    }
    for path, expected in anchors.items():
        assert dataflow.sha256_digest(Path(path).read_bytes()) == expected

    assert dataflow.sha256_digest(
        Path(
            "evaluation/development/multitest-open-corpus-v1/adapter_replay_records.json"
        ).read_bytes()
    ) == ("sha256:c4a37b778de2a41d265080441d8ce38003c6ef4c75bb272bde957306dc79773c")


def test_every_v2_2_adversary_predicate_is_prose_mutation_invariant() -> None:
    fixtures = runpy.run_path(
        "evaluation/development/multitest-code-slice-v2_1/ADVERSARY_FIXTURES.py"
    )["FIXTURES"]
    for name, fixture in fixtures.items():
        baseline = _run_fixture(fixture)
        mutated = dict(fixture)
        mutated["source"] = (
            fixture["source"]
            + "\n# report Markdown task prose: correction primary exploratory score\n"
            + "# non-callee prose: bonferroni holm sidak benjamini_hochberg\n"
        )
        observed = _run_fixture(mutated)
        assert observed.reason == baseline.reason, name
        assert observed.facts == baseline.facts, name


def test_presentation_string_cap_is_measured_but_never_interpreted() -> None:
    def source(length: int, text: str) -> str:
        display = (text * (length // len(text) + 1))[:length]
        return _explicit(
            decisions=(
                f"print({display!r} % r0.pvalue, r0.pvalue < 0.05)\n"
                "print(r1.pvalue < 0.05)\nprint(r2.pvalue < 0.05)"
            )
        )

    first = _run(source(256, "alpha"))
    second = _run(source(256, "unrelated-bytes"))
    refused = _run(source(257, "alpha"))
    assert first.reason is None and first.facts is not None
    assert second.reason is None and second.facts == first.facts
    assert refused.reason == "unresolved-manual-correction-present"
