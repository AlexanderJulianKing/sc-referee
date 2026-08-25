from __future__ import annotations

import ast
import json
import re
import runpy
from pathlib import Path

import pytest

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v1 as dataflow
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


def test_unsupported_correction_return_abstains_and_never_classifies_none() -> None:
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
    assert result.facts is None
    assert result.reason == "correction-family-lineage-unresolved"


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

    assert result.reason is None


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
    "threshold",
    [
        "0.05 / 3",
        "1 - (1 - 0.05) ** (1 / 3)",
        "ALPHA",
        "thresholds[0]",
        "make_threshold()",
    ],
)
def test_computed_or_unresolved_thresholds_abstain(threshold: str) -> None:
    setup = "ALPHA = 0.05\nthresholds = [0.05]\ndef make_threshold():\n    return 0.05\n"
    decisions = "\n".join(f"print(r{i}.pvalue < {threshold})" for i in range(3))
    assert _run(setup + _explicit(decisions=decisions)).reason == "unresolved-decision-threshold"


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


def test_sensitivity_duplicate_stops_before_operand_resolution() -> None:
    source = _explicit(
        before=(
            'unused = stats.ttest_ind(df.loc[df["group"] == "a", "missing"], '
            'df.loc[df["group"] == "b", "missing"])\n'
        )
    )
    assert _run(source).reason == "extra-registered-test-outside-authorized-family"


def test_discovery_validation_split_abstains_on_row_completeness() -> None:
    selection = 'df.loc[(df["group"] == "{group}") & (df["{column}"] > 0), "{column}"]'
    assert _run(_explicit(selection=selection)).reason == "selected-group-row-completeness-unproven"


def test_exact_literal_query_is_the_only_additional_row_mask_exemption() -> None:
    selection = 'df.query("group == \'{group}\'")["{column}"]'
    assert _run(_explicit(selection=selection)).reason is None


def test_boolean_mask_subscript_is_never_query_exempt() -> None:
    selection = 'df[df["group"] == "{group}"]["{column}"]'
    assert _run(_explicit(selection=selection)).reason == "selected-group-row-completeness-unproven"


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


@pytest.mark.parametrize("probability", ["0.99", "0.995"])
def test_t_ppf_mirrored_bonferroni_product_rule_uses_source_decimal(probability: str) -> None:
    columns = ("m1", "m2", "m3", "m4", "m5")
    source = _explicit(
        columns=columns,
        after=f"print(stats.t.ppf({probability}, len(df) - 2))\n",
    )
    assert _run(source, columns).reason == "unresolved-inference-sibling-present"


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


def test_statistics_prefix_registry_is_byte_equal_to_qualified_v3_1() -> None:
    source = __import__(
        "sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1",
        fromlist=["_STATISTICS_PREFIXES"],
    )._STATISTICS_PREFIXES
    assert dataflow._STATISTICS_PREFIXES == source


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
    assert all(len(set(items)) == 2 for items in counts if len(items) == 3)
    assert terminal_slots == []


def test_answer_visible_guard_fixture_corpus_is_canonical_and_guard_isolated() -> None:
    root = Path("evaluation/development/multitest-code-slice-v1")
    payload = (root / "DEVELOPMENT_LEDGER.json").read_bytes()
    ledger = json.loads(payload)
    assert canonical_json(ledger).encode() == payload.rstrip(b"\n")
    namespace = runpy.run_path(str(root / "GUARD_FIXTURES.py"))
    fixtures = namespace["FIXTURES"]
    assert ledger["fixture_count"] == len(fixtures) == 17
    assert [item["name"] for item in ledger["fixtures"]] == list(fixtures)
    for record in ledger["fixtures"]:
        fixture = fixtures[record["name"]]
        result = _run(fixture["source"], fixture["columns"])
        outcome = (
            "covered-negative"
            if result.reason is None
            and result.facts is not None
            and result.facts.correction_classification == "complete"
            else result.reason
        )
        assert fixture["expected"] == record["expected"] == outcome
