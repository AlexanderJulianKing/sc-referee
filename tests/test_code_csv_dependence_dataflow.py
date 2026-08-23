from __future__ import annotations

import pytest

import sc_referee.scientific_checks.code_csv_dependence_dataflow as dataflow_module
from sc_referee.scientific_checks.code_csv_dependence_dataflow import (
    analyze_code_csv_dataflow,
)

_HEADER = ("unit", "group", "visit", "value")
_GROUPS = ("A", "B")


def _source(
    *,
    reader: str = 'df = pd.read_csv("data.csv")',
    left: str = 'left = df.loc[df["group"] == "A", "value"]',
    right: str = 'right = df.loc[df["group"] == "B", "value"]',
    test: str = "result = stats.ttest_ind(left, right)",
    before_test: str = "",
    after_test: str = "",
    sink: str = "print(result.pvalue)",
) -> bytes:
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{reader}\n"
        f"{left}\n"
        f"{right}\n"
        f"{before_test}\n"
        f"{test}\n"
        f"{after_test}\n"
        f"{sink}\n"
    ).encode()


def _analyze(source: bytes):  # type: ignore[no-untyped-def]
    return analyze_code_csv_dataflow(
        source,
        authorized_path="data.csv",
        unit_column="unit",
        group_column="group",
        csv_header=_HEADER,
        group_values=_GROUPS,
    )


@pytest.mark.parametrize(
    ("left", "right", "selection_kind"),
    [
        (
            'left = df.loc[df["group"] == "A", "value"]',
            'right = df.loc[df["group"] == "B", "value"]',
            "pandas_loc_boolean_mask_v1",
        ),
        (
            'left = df[df["group"] == "A"]["value"]',
            'right = df[df["group"] == "B"]["value"]',
            "pandas_boolean_mask_v1",
        ),
        (
            'left = df.query("group == \'A\'")["value"]',
            'right = df.query("group == \'B\'")["value"]',
            "pandas_query_v1",
        ),
    ],
)
def test_exact_pandas_selection_forms_are_complete(
    left: str, right: str, selection_kind: str
) -> None:
    result = _analyze(_source(left=left, right=right))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.selection_kinds == (selection_kind, selection_kind)
    assert result.facts.group_values == _GROUPS
    assert result.facts.value_column == "value"
    assert result.facts.output_sink_kinds == ("builtin_print",)


def test_groupby_get_group_is_selection_not_aggregation() -> None:
    source = _source(
        left='grouped = df.groupby("group")\nleft = grouped.get_group("A")["value"]',
        right='right = grouped.get_group("B")["value"]',
    )
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.selection_kinds == (
        "pandas_groupby_get_group_v1",
        "pandas_groupby_get_group_v1",
    )


def test_exact_numpy_named_array_reader_and_selection() -> None:
    source = (
        b"import numpy as np\n"
        b"from scipy import stats\n"
        b'df = np.genfromtxt("data.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")\n'
        b'left = df[df["group"] == "A"]["value"]\n'
        b'right = df[df["group"] == "B"]["value"]\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.reader_api == "numpy_genfromtxt_named_csv_v1"
    assert result.facts.selection_kinds == (
        "numpy_named_boolean_mask_v1",
        "numpy_named_boolean_mask_v1",
    )


def test_numpy_reader_does_not_admit_pandas_only_selection_syntax() -> None:
    source = (
        b"import numpy as np\n"
        b"from scipy import stats\n"
        b'df = np.genfromtxt("data.csv", delimiter=",", names=True, dtype=None, encoding="utf-8")\n'
        b'left = df.loc[df["group"] == "A", "value"]\n'
        b'right = df.loc[df["group"] == "B", "value"]\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "two-group-row-selection-unavailable"


@pytest.mark.parametrize(
    ("test", "procedure", "variant"),
    [
        ("result = stats.ttest_ind(left, right)", "scipy.stats.ttest_ind", "student"),
        (
            "result = stats.ttest_ind(left, right, equal_var=True)",
            "scipy.stats.ttest_ind",
            "student",
        ),
        (
            "result = stats.ttest_ind(left, right, equal_var=False)",
            "scipy.stats.ttest_ind",
            "welch",
        ),
        (
            'result = stats.mannwhitneyu(left, right, alternative="two-sided")',
            "scipy.stats.mannwhitneyu",
            "mannwhitneyu",
        ),
    ],
)
def test_registered_test_variants(test: str, procedure: str, variant: str) -> None:
    result = _analyze(_source(test=test))
    assert result.reason is None
    assert result.facts is not None
    assert (result.facts.procedure_id, result.facts.procedure_variant) == (
        procedure,
        variant,
    )


def test_two_name_result_and_p_name_sink() -> None:
    result = _analyze(
        _source(test="statistic, p_value = stats.ttest_ind(left, right)", sink="print(p_value)")
    )
    assert result.reason is None
    assert result.facts is not None


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ('df["group"] = pd.Categorical(df["group"])', "tracked-value-mutation"),
        ('summary = df.groupby("unit").mean()', "aggregation-on-test-operand-path"),
    ],
)
def test_mutation_and_aggregation_precedence(mutation: str, reason: str) -> None:
    if reason == "aggregation-on-test-operand-path":
        source = _source(
            left=(f'{mutation}\nleft = summary.loc[summary["group"] == "A", "value"]'),
            right='right = summary.loc[summary["group"] == "B", "value"]',
        )
    else:
        source = _source(before_test=mutation)
    assert _analyze(source).reason == reason


def test_second_accepted_reader_abstains_before_candidate_ranking() -> None:
    source = _source(before_test='other = pd.read_csv("summary.csv")')
    assert _analyze(source).reason == "additional-accepted-reader-present"


def test_dependence_aware_sibling_abstains_without_prose() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"import statsmodels.formula.api as smf\n"
        b'df = pd.read_csv("data.csv")\n'
        b'left = df.loc[df["group"] == "A", "value"]\n'
        b'right = df.loc[df["group"] == "B", "value"]\n'
        b'mixed = smf.mixedlm("value ~ group", data=df, groups=df["unit"])\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "dependence-aware-sibling-present"


def test_sink_reaching_unregistered_component_call_abstains() -> None:
    source = _source(after_test="other = custom_model(df)", sink="print(result.pvalue, other)")
    assert _analyze(source).reason == "unregistered-component-consumer"


def test_result_without_p_output_abstains() -> None:
    assert _analyze(_source(sink='print("done")')).reason == ("test-result-output-sink-unavailable")


def test_e14_e15_descriptive_loop_is_order_independent_and_non_evidentiary() -> None:
    loop = (
        'for label, values in (("A", left), ("B", right)):\n'
        '    print(f"{label}: {len(values)} {values.mean()} {values.std(ddof=1)}")'
    )
    before = _analyze(_source(before_test=loop))
    after = _analyze(_source(after_test=loop))
    for result in (before, after):
        assert result.reason is None
        assert result.facts is not None
        assert result.facts.descriptive_loop_count == 1


@pytest.mark.parametrize(
    ("loop", "expected_reason"),
    [
        (
            "for label, values in make_groups(left, right):\n    print(label, values.mean())",
            "unregistered-component-consumer",
        ),
        ('for label, values in (("A", left), ("B", right)):\n    saved = values.mean()', None),
        (
            'for label, values in (("A", left), ("B", right)):\n    print(custom(values))',
            "unregistered-component-consumer",
        ),
    ],
)
def test_v2_loop_admission_is_directional(loop: str, expected_reason: str | None) -> None:
    assert _analyze(_source(before_test=loop)).reason == expected_reason


def test_comments_docstrings_and_printed_labels_do_not_change_code_classification() -> None:
    source = (
        '"""exploratory aggregation pseudoreplication prose"""\n'
        + _source(sink='print("no averaging was applied", result.pvalue)').decode()
    ).encode()
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None


@pytest.mark.parametrize(
    ("imports", "setup", "reader"),
    [
        (
            "import os",
            'FINAL = "data.csv"',
            "df = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), FINAL))",
        ),
        (
            "import os.path",
            'BASE = os.path.dirname(os.path.abspath(__file__))\nFINAL = "data.csv"',
            "df = pd.read_csv(os.path.join(BASE, FINAL))",
        ),
        (
            "import pathlib",
            'FINAL = "data.csv"',
            "df = pd.read_csv(pathlib.Path(__file__).resolve().parent / FINAL)",
        ),
        (
            "from pathlib import Path",
            'BASE = Path(__file__).parent\nFINAL = "data.csv"',
            "df = pd.read_csv(BASE / FINAL)",
        ),
    ],
)
def test_x1_exact_file_parent_paths(imports: str, setup: str, reader: str) -> None:
    source = (
        _source(reader=reader)
        .decode()
        .replace("import pandas as pd\n", f"import pandas as pd\n{imports}\n{setup}\n")
    )
    assert _analyze(source.encode()).reason is None


@pytest.mark.parametrize(
    "reader",
    [
        'df = pd.read_csv(Path(__file__).parent.parent / "data.csv")',
        'df = pd.read_csv(Path(__file__).parents[0] / "data.csv")',
        'df = pd.read_csv(Path(__file__).absolute().parent / "data.csv")',
        'df = pd.read_csv(Path(__file__).parent.joinpath("data.csv"))',
        'df = pd.read_csv(Path(__file__).parent / "extra" / "data.csv")',
        'df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.csv"))',
    ],
)
def test_x1_whole_expression_refusals(reader: str) -> None:
    source = (
        _source(reader=reader)
        .decode()
        .replace(
            "import pandas as pd\n", "import pandas as pd\nimport os\nfrom pathlib import Path\n"
        )
    )
    assert _analyze(source.encode()).reason == "authorized-reader-lineage-unavailable"


def test_x2_statistic_is_legal_consumer_but_never_the_required_p_sink() -> None:
    only_statistic = _source(sink="print(result.statistic)")
    assert _analyze(only_statistic).reason == "test-result-output-sink-unavailable"
    both = _source(sink="print(result.statistic)\nprint(result.pvalue)")
    assert _analyze(both).reason is None


@pytest.mark.parametrize(
    "reduction",
    [
        "left.mean()",
        "left.std()",
        "left.std(ddof=1)",
        "left.median()",
        "left.min()",
        "left.max()",
        "left.count()",
        "left.sum()",
        "len(left)",
        "sum(left)",
        "min(left)",
        "max(left)",
        "round(left.mean())",
        "round(left.mean(), 2)",
    ],
)
def test_x3_every_straight_descriptive_reduction(reduction: str) -> None:
    result = _analyze(
        _source(
            before_test=f"description = {reduction}",
            sink='print("{}".format(description))\nprint(result.pvalue)',
        )
    )
    assert result.reason is None


def test_x3_format_allows_only_names_literals_and_group_constants() -> None:
    source = _source(
        before_test='GROUP_LABEL = "A"\ndescription = left.mean()',
        sink='print("{} {} {}".format(description, GROUP_LABEL, 2))\nprint(result.pvalue)',
    )
    assert _analyze(source).reason is None
    direct_arithmetic = _source(
        before_test="description = left.mean()",
        sink='print("{}".format(description - 2))\nprint(result.pvalue)',
    )
    assert _analyze(direct_arithmetic).reason is None


def test_a3_pretest_aggregated_description_is_output_only() -> None:
    source = _source(
        before_test='summary = df.groupby("unit").mean()\ndescription = summary.mean()',
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is None


def _helper_source(
    helper: str,
    *,
    reader: str = "df = load()",
    extra_main: str = "",
) -> bytes:
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        'DATA_FILE = "data.csv"\n'
        f"{helper}\n"
        "def main():\n"
        f"    {reader}\n"
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        f"{extra_main}"
        "    result = stats.ttest_ind(left, right)\n"
        "    print(result.pvalue)\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    ).encode()


def test_x4a_literal_and_closed_module_defaults_inline() -> None:
    helper = "def load(path=DATA_FILE):\n    return pd.read_csv(path)\n"
    assert _analyze(_helper_source(helper)).reason is None
    literal = helper.replace("DATA_FILE", '"data.csv"')
    assert _analyze(_helper_source(literal)).reason is None


def test_x4_selector_and_test_helpers_inline_to_depth_two() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b'def load():\n    return pd.read_csv("data.csv")\n'
        b'def select(df, label):\n    return df.loc[df["group"] == label, "value"]\n'
        b"def compare(left, right):\n    return stats.ttest_ind(left, right)\n"
        b"def main():\n"
        b"    df = load()\n"
        b'    left = select(df, "A")\n'
        b'    right = select(df, "B")\n'
        b"    result = compare(left, right)\n"
        b"    print(result.pvalue)\n"
        b'if __name__ == "__main__":\n    main()\n'
    )
    assert _analyze(source).reason is None


def _descriptive_helper_source(
    helper: str,
    *,
    extra_main: str,
    sink: str = "print(result.pvalue)",
) -> bytes:
    return (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{helper}\n"
        "def main():\n"
        '    df = pd.read_csv("data.csv")\n'
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        f"{extra_main}"
        "    result = stats.ttest_ind(left, right)\n"
        f"    {sink}\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    ).encode()


@pytest.mark.parametrize(
    ("returned", "consumer"),
    [
        ("mean_value", 'print("{}".format(description))'),
        ('{"mean": mean_value}', 'print("{}".format(description["mean"]))'),
        ("(mean_value,)", 'print(f"{description[0]}")'),
        ("[mean_value]", "print(description[0])"),
    ],
)
def test_x5_scalar_and_container_shapes_are_print_only(returned: str, consumer: str) -> None:
    helper = f"def describe(values):\n    mean_value = values.mean()\n    return {returned}\n"
    source = _descriptive_helper_source(
        helper,
        extra_main=f"    description = describe(left)\n    {consumer}\n",
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    ("extra_main", "helper_return"),
    [
        (
            '    print(description["mean"])\n    description = describe(left)\n',
            '{"mean": mean_value}',
        ),
        ("    describe(left)\n", "mean_value"),
        ('    description = describe(left)\n    print(f"{description!r}")\n', "mean_value"),
        ('    description = describe(left)\n    print(description, sep="")\n', "mean_value"),
        (
            "    description = describe(left)\n    print(description, dynamic_label)\n",
            "mean_value",
        ),
    ],
)
def test_v2_output_only_helper_uses_retire_x5_terminal_refusals(
    extra_main: str, helper_return: str
) -> None:
    helper = f"def describe(values):\n    mean_value = values.mean()\n    return {helper_return}\n"
    source = _descriptive_helper_source(helper, extra_main=extra_main)
    assert _analyze(source).reason is None


def test_v2_output_only_computed_scalar_is_admitted() -> None:
    helper = "def describe(values):\n    unused = values.mean()\n    return 1 + 2\n"
    source = _descriptive_helper_source(
        helper,
        extra_main="    description = describe(left)\n    print(description)\n",
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize("size", [1, 16])
def test_x5_container_member_boundaries(size: int) -> None:
    values = ", ".join(f'"k{index}": mean_value' for index in range(size))
    helper = f"def describe(values):\n    mean_value = values.mean()\n    return {{{values}}}\n"
    source = _descriptive_helper_source(
        helper,
        extra_main='    description = describe(left)\n    print(description["k0"])\n',
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    "returned",
    [
        "{}",
        "{" + ", ".join(f'"k{index}": mean_value' for index in range(17)) + "}",
        '{"a": mean_value, "a": mean_value}',
        "{GROUP_LABEL.lower(): mean_value}",
        '{"outer": {"inner": mean_value}}',
        "(*[mean_value],)",
    ],
)
def test_v2_output_only_container_shapes_do_not_define_operand_edges(returned: str) -> None:
    helper = f"def describe(values):\n    mean_value = values.mean()\n    return {returned}\n"
    source = _descriptive_helper_source(
        helper,
        extra_main="    description = describe(left)\n    print(description)\n",
    ).decode()
    if "GROUP_LABEL" in returned:
        source = source.replace(
            "from scipy import stats\n", 'from scipy import stats\nGROUP_LABEL = "A"\n'
        )
    assert _analyze(source.encode()).reason is None


@pytest.mark.parametrize(
    ("use", "expected_reason"),
    [
        ('left = description["mean"]', "two-group-row-selection-unavailable"),
        (
            'other = stats.ttest_ind(description["mean"], right)',
            "aggregated-sibling-test-present",
        ),
        ('other = pd.read_csv(description["mean"])', "additional-accepted-reader-present"),
        ('other = custom(description["mean"])', "unregistered-component-consumer"),
        ('if description["mean"]:\n        print("yes")', None),
        ("for item in description:\n        print(item)", None),
        ('other = description["mean"] > 0', None),
        ('description["mean"] = 0', "tracked-value-mutation"),
        ('Path("out.txt").write_text(str(description["mean"]), encoding="utf-8")', None),
        ('text = "{}".format(description["mean"])', None),
    ],
)
def test_v2_helper_member_edges_are_guarded_only_when_protected(
    use: str, expected_reason: str | None
) -> None:
    helper = (
        'def describe(values):\n    mean_value = values.mean()\n    return {"mean": mean_value}\n'
    )
    source = _descriptive_helper_source(
        helper,
        extra_main=f"    description = describe(left)\n    {use}\n",
    ).decode()
    source = source.replace(
        "import pandas as pd\n", "import pandas as pd\nfrom pathlib import Path\n"
    )
    assert _analyze(source.encode()).reason == expected_reason


def test_a3_inlined_pretest_aggregation_is_admitted_only_as_description() -> None:
    helper = (
        "def describe(values):\n"
        '    summary = values.groupby("unit").mean()\n'
        "    mean_value = summary.mean()\n"
        '    return {"mean": mean_value}\n'
    )
    source = _descriptive_helper_source(
        helper,
        extra_main='    description = describe(left)\n    print(description["mean"])\n',
    )
    assert _analyze(source).reason is None


def test_x5_dict_return_reaching_test_argument_abstains() -> None:
    helper = (
        'def describe(values):\n    mean_value = values.mean()\n    return {"mean": mean_value}\n'
    )
    source = _descriptive_helper_source(
        helper,
        extra_main=('    description = describe(left)\n    left = description["mean"]\n'),
    )
    assert _analyze(source).reason == "two-group-row-selection-unavailable"


def test_x5_helper_mixing_reductions_with_registered_test_abstains() -> None:
    helper = (
        "def describe(values, other):\n"
        "    mean_value = values.mean()\n"
        "    inner = stats.ttest_ind(values, other)\n"
        '    return {"mean": mean_value, "p": inner.pvalue}\n'
    )
    source = _descriptive_helper_source(
        helper,
        extra_main='    description = describe(left, right)\n    print(description["mean"])\n',
    )
    assert _analyze(source).reason == "multiple-rowwise-test-candidates"


@pytest.mark.parametrize("operator", ["+", "-", "*", "/", "//", "%", "**"])
def test_x6_every_arithmetic_operator_is_print_only(operator: str) -> None:
    source = _source(
        before_test="description = len(left)",
        sink=(f'print("{{}}".format(description {operator} 2))\nprint(result.pvalue)'),
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    ("argument", "expected_reason"),
    [
        ("round(description)", None),
        ("description.real", "admission-call-off-list"),
        ("description[0]", "admission-call-off-list"),
        ("description > 0", None),
        ("[description]", None),
        ("description if True else 0", None),
        ("missing + description", None),
    ],
)
def test_v2_print_only_expressions_follow_closed_read_rules(
    argument: str, expected_reason: str | None
) -> None:
    source = _source(
        before_test="description = len(left)",
        sink=f'print("{{}}".format({argument}))\nprint(result.pvalue)',
    )
    assert _analyze(source).reason == expected_reason


def test_x5_x6_never_supply_the_required_p_result_sink() -> None:
    helper = "def describe(values):\n    mean_value = values.mean()\n    return mean_value\n"
    source = _descriptive_helper_source(
        helper,
        extra_main='    description = describe(left)\n    print("{}".format(description - 2))\n',
        sink='print("done")',
    )
    assert _analyze(source).reason == "test-result-output-sink-unavailable"


@pytest.mark.parametrize(
    "expression",
    [
        "int(left.mean())",
        "float(left.mean())",
        "int(left.mean() + 1)",
        "float(left.mean() + left.std())",
    ],
)
def test_x7_depth_one_numeric_wrappers_are_descriptive_only(expression: str) -> None:
    result = _analyze(
        _source(
            before_test=f"description = {expression}",
            sink="print(description)\nprint(result.pvalue)",
        )
    )
    assert result.reason is None


@pytest.mark.parametrize(
    ("expression", "expected_reason"),
    [
        ("int(float(left.mean()))", None),
        ("float(int(left.mean()))", None),
        ("int(left.mean(), 2)", "unregistered-component-consumer"),
        ("float(x=left.mean())", "unregistered-component-consumer"),
    ],
)
def test_v2_nested_closed_numeric_wrappers_are_independently_classified(
    expression: str, expected_reason: str | None
) -> None:
    result = _analyze(
        _source(
            before_test=f"description = {expression}",
            sink="print(description)\nprint(result.pvalue)",
        )
    )
    assert result.reason == expected_reason


@pytest.mark.parametrize("name", ["int", "float"])
def test_x7_numeric_wrappers_require_unshadowed_builtins(name: str) -> None:
    source = _source(before_test=f"{name} = custom\ndescription = {name}(left.mean())")
    assert _analyze(source).reason == "api-resolution-ambiguous"


@pytest.mark.parametrize("expression", ["left.var()", "left.var(ddof=0)", "left.var(ddof=1)"])
def test_x7_var_exact_signatures_are_descriptive(expression: str) -> None:
    result = _analyze(
        _source(
            before_test=f"description = {expression}",
            sink="print(description)\nprint(result.pvalue)",
        )
    )
    assert result.reason is None


@pytest.mark.parametrize(
    "expression",
    ["left.var(1)", "left.var(skipna=True)"],
)
def test_x7_var_other_signatures_abstain(expression: str) -> None:
    source = _source(
        before_test=f"description = {expression}",
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is not None


@pytest.mark.parametrize(
    "expression",
    ["left.size", "left.shape[0]", "left.shape[1]", "left.nunique()", "df.size"],
)
def test_x7_count_family_shapes_are_descriptive(expression: str) -> None:
    result = _analyze(
        _source(
            before_test=f"description = {expression}",
            sink="print(description)\nprint(result.pvalue)",
        )
    )
    assert result.reason is None


@pytest.mark.parametrize(
    "expression",
    ["left.shape[-1]", "left.nunique(1)"],
)
def test_x7_count_family_near_misses_abstain(expression: str) -> None:
    source = _source(
        before_test=f"description = {expression}",
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is not None


@pytest.mark.parametrize("target", ["n_left, n_right", "[n_left, n_right]"])
def test_x7_literal_tuple_destructuring_binds_independent_descriptives(target: str) -> None:
    result = _analyze(
        _source(
            before_test=f"{target} = (len(left), len(right))",
            sink="print(n_left, n_right)\nprint(result.pvalue)",
        )
    )
    assert result.reason is None


@pytest.mark.parametrize(
    ("before_test", "expected_reason"),
    [
        (
            'grouped = df.groupby("group")\nname, values = grouped',
            "admission-slice-reaches-operand",
        ),
        (
            "packed = stats.ttest_ind(left, right)\nstatistic, probability = "
            "(packed.statistic, packed.pvalue)",
            "multiple-rowwise-test-candidates",
        ),
    ],
)
def test_x7_destructuring_does_not_admit_groupby_or_test_result_pairs(
    before_test: str, expected_reason: str
) -> None:
    assert _analyze(_source(before_test=before_test)).reason == expected_reason


def test_x7_direct_reductions_may_appear_inside_descriptive_arithmetic() -> None:
    result = _analyze(
        _source(
            before_test="description = left.mean() - (left.std() + left.var(ddof=1))",
            sink='print("{}".format(description))\nprint(result.pvalue)',
        )
    )
    assert result.reason is None


def test_a3_mixed_pretest_reductions_are_output_only() -> None:
    source = _source(
        before_test=(
            'summary = df.groupby("unit").mean()\ndescription = left.mean() + summary.mean()'
        ),
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is None


def test_x7_constant_only_subtree_is_neutral_inside_x6_arithmetic() -> None:
    result = _analyze(
        _source(
            before_test="description = len(left)",
            sink='print("{}".format(description - (1 + 1)))\nprint(result.pvalue)',
        )
    )
    assert result.reason is None


def test_x7_constant_fstring_format_spec_is_a_closed_x5_terminal() -> None:
    helper = "def describe(values):\n    return values.mean()\n"
    source = _descriptive_helper_source(
        helper,
        extra_main='    description = describe(left)\n    print(f"{description:.2f}")\n',
    )
    assert _analyze(source).reason is None


def test_v2_nested_fstring_is_print_only_and_not_an_operand_edge() -> None:
    helper = "def describe(values):\n    return values.mean()\n"
    source = _descriptive_helper_source(
        helper,
        extra_main=(
            '    width = 2\n    description = describe(left)\n    print(f"{description:{width}}")\n'
        ),
    )
    assert _analyze(source).reason is None


def test_v2_percent_format_labels_do_not_control_admission() -> None:
    helper = "def describe(values):\n    return values.mean()\n"
    accepted = _descriptive_helper_source(
        helper,
        extra_main=(
            '    GROUP_LABEL = "A"\n'
            "    description = describe(left)\n"
            '    print("%s %.2f" % (GROUP_LABEL, description))\n'
        ),
    )
    assert _analyze(accepted).reason is None
    refused = _descriptive_helper_source(
        helper,
        extra_main=(
            "    description = describe(left)\n"
            '    print("%s %.2f" % (dynamic_label, description))\n'
        ),
    )
    assert _analyze(refused).reason is None


def test_x7_helper_name_return_var_and_embedded_reductions_are_descriptive() -> None:
    helper = "def describe(values):\n    variance = values.var(ddof=1)\n    return variance\n"
    source = _descriptive_helper_source(
        helper,
        extra_main="    description = describe(left)\n    print(description)\n",
    )
    assert _analyze(source).reason is None

    embedded = "def describe(values):\n    return int(values.count()) + float(values.mean())\n"
    source = _descriptive_helper_source(
        embedded,
        extra_main="    description = describe(left)\n    print(description)\n",
    )
    assert _analyze(source).reason is None


def test_x7_helper_literal_tuple_assignment_is_closed_element_by_element() -> None:
    helper = (
        "def describe(values):\n"
        "    sample_size, variance = (int(values.count()), values.var(ddof=1))\n"
        '    return {"n": sample_size, "variance": variance}\n'
    )
    source = _descriptive_helper_source(
        helper,
        extra_main=(
            "    description = describe(left)\n"
            '    print(description["n"], description["variance"])\n'
        ),
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    ("helper", "reason"),
    [
        (
            "def load(path=make_path()):\n    return pd.read_csv(path)\n",
            "helper-parameter-default-unsupported",
        ),
        (
            "def load(path: str = DATA_FILE) -> pd.DataFrame:\n    return pd.read_csv(path)\n",
            None,
        ),
        (
            "def load(*paths):\n    return pd.read_csv(paths[0])\n",
            "helper-variadic-parameter-unsupported",
        ),
        (
            "def load(path):\n    return pd.read_csv(path)\n",
            "helper-argument-binding-unsupported",
        ),
        (
            'def load():\n    return {"frame": pd.read_csv(DATA_FILE)}\n',
            "authorized-reader-lineage-unavailable",
        ),
        (
            "def load():\n    value = missing_name\n    return pd.read_csv(DATA_FILE)\n",
            "helper-free-name-unbound",
        ),
        (
            "def load():\n    if True:\n        frame = pd.read_csv(DATA_FILE)\n    return frame\n",
            None,
        ),
        (
            "def load():\n    return load()\n",
            "helper-recursion-unsupported",
        ),
    ],
)
def test_x4_closed_helper_abstention_codes(helper: str, reason: str | None) -> None:
    assert _analyze(_helper_source(helper)).reason == reason


def test_x4_parameter_shadowing_abstains() -> None:
    source = _helper_source(
        "def load(pd):\n    return pd.read_csv(DATA_FILE)\n",
        reader="df = load(pd)",
    )
    assert _analyze(source).reason == "helper-parameter-shape-unsupported"


def test_a1_helper_and_main_annotations_add_no_runtime_edge() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"def load(path: unresolved.Annotation(call())) -> pd.DataFrame:\n"
        b"    return pd.read_csv(path)\n"
        b"def main() -> unresolved.Result(factory()):\n"
        b'    df = load("data.csv")\n'
        b'    left = df.loc[df["group"] == "A", "value"]\n'
        b'    right = df.loc[df["group"] == "B", "value"]\n'
        b"    result = stats.ttest_ind(left, right)\n"
        b"    print(result.pvalue)\n"
        b'if __name__ == "__main__":\n    main()\n'
    )
    assert _analyze(source).reason is None


def test_a1_annotated_helper_aggregation_stays_on_operand_path() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"def load(path: str) -> pd.DataFrame:\n    return pd.read_csv(path)\n"
        b"def pseudobulk(frame: pd.DataFrame) -> pd.DataFrame:\n"
        b'    summary = frame.groupby(["unit", "group"], as_index=False)["value"].mean()\n'
        b"    return summary\n"
        b"def main() -> None:\n"
        b'    frame = load("data.csv")\n'
        b"    summary = pseudobulk(frame)\n"
        b'    left = summary.loc[summary["group"] == "A", "value"]\n'
        b'    right = summary.loc[summary["group"] == "B", "value"]\n'
        b"    result = stats.ttest_ind(left, right)\n"
        b"    print(result.pvalue)\n"
        b'if __name__ == "__main__":\n    main()\n'
    )
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    ("binding", "helper", "call"),
    [
        (
            'LABEL = "A"',
            "def describe(LABEL):\n    return str(LABEL)",
            "description = describe(LABEL)",
        ),
        (
            "LIMIT = 2",
            "def describe(LIMIT):\n    return int(LIMIT)",
            "description = describe(LIMIT)",
        ),
        (
            'LABELS = ("A", "B")',
            "def describe(LABELS):\n    return len(LABELS)",
            "description = describe(LABELS)",
        ),
    ],
)
def test_a2_alpha_renaming_allows_closed_constant_parameter_spellings(
    binding: str, helper: str, call: str
) -> None:
    source = (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{binding}\n"
        f"{helper}\n"
        "def main():\n"
        '    df = pd.read_csv("data.csv")\n'
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        f"    {call}\n"
        "    print(description)\n"
        "    result = stats.ttest_ind(left, right)\n"
        "    print(result.pvalue)\n"
        'if __name__ == "__main__":\n    main()\n'
    ).encode()
    assert _analyze(source).reason is None


def test_a3_pretest_output_only_groupby_aggregation_is_directional() -> None:
    source = _source(
        before_test=(
            'summary = df.groupby("group")["value"].agg(["mean", "std"])\n'
            "print(summary.to_string())"
        )
    )
    assert _analyze(source).reason is None


def test_a3_pretest_groupby_aggregation_feeding_operand_still_abstains() -> None:
    source = _source(
        left=(
            'summary = df.groupby(["unit", "group"], as_index=False)["value"].agg("mean")\n'
            'left = summary.loc[summary["group"] == "A", "value"]'
        ),
        right='right = summary.loc[summary["group"] == "B", "value"]',
    )
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    "description",
    [
        'description = df.groupby("group")["value"].agg("mean").reindex(["A", "B"])',
        'description = df.groupby("group")["value"].agg("mean").reindex(index=["A", "B"])',
        'description = df.groupby(["group", "visit"])["value"].mean().unstack()',
        'description = df.groupby(["group", "visit"])["value"].mean().unstack("group")',
        'description = df.groupby(["group", "visit"])["value"].mean().unstack(level=0)',
        "description = left.to_numpy()",
        'description = left.to_numpy(dtype="float64")',
    ],
)
def test_a4_closed_pandas_readonly_shapes_are_descriptive(description: str) -> None:
    source = _source(
        before_test=description,
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    "description",
    [
        'description = df.reindex(["A"], columns=["value"])',
        "description = df.reindex(dynamic_labels)",
        'description = df.unstack("group", 0)',
        "description = df.unstack(level=LEVEL)",
        "description = left.to_numpy(copy=True)",
    ],
)
def test_a4_pandas_readonly_near_misses_abstain(description: str) -> None:
    source = _source(
        before_test=description,
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason == "unregistered-component-consumer"


@pytest.mark.parametrize(
    "conversion",
    [
        ".to_numpy()",
        '.to_numpy(dtype="float64")',
        '.to_numpy("float64")',
    ],
)
def test_g3_to_numpy_preserves_test_operand_provenance(conversion: str) -> None:
    source = _source(
        left=f'left = df.loc[df["group"] == "A", "value"]{conversion}',
        right=f'right = df.loc[df["group"] == "B", "value"]{conversion}',
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    "conversion",
    [
        ".to_numpy(copy=True)",
        ".to_numpy(dtype=dynamic_dtype)",
        '.to_numpy("float64", na_value=0)',
    ],
)
def test_g3_to_numpy_operand_near_misses_abstain(conversion: str) -> None:
    source = _source(
        left=f'left = df.loc[df["group"] == "A", "value"]{conversion}',
        right=f'right = df.loc[df["group"] == "B", "value"]{conversion}',
    )
    assert _analyze(source).reason == "unregistered-component-consumer"


def test_g4_contract_domain_dict_comprehension_reconstructs_operand_members() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b'GROUPS = ("A", "B")\n'
        b'df = pd.read_csv("data.csv")\n'
        b'vectors = {level: df.loc[df["group"] == level, "value"] for level in GROUPS}\n'
        b'result = stats.ttest_ind(vectors["A"], vectors["B"])\n'
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason is None


def test_g4_dict_comprehension_aggregate_members_stay_on_operand_path() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b'GROUPS = ("A", "B")\n'
        b'df = pd.read_csv("data.csv")\n'
        b'vectors = {level: df.loc[df["group"] == level, "value"].mean() '
        b"for level in GROUPS}\n"
        b'result = stats.ttest_ind(vectors["A"], vectors["B"])\n'
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "rowwise-two-sample-test-unavailable"


def test_g5_module_list_constants_bind_contract_domain_loop() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b'GROUPS = ["A", "B"]\n'
        b'df = pd.read_csv("data.csv")\n'
        b"vectors = {}\n"
        b"for level in GROUPS:\n"
        b'    vectors[level] = df.loc[df["group"] == level, "value"]\n'
        b'result = stats.ttest_ind(vectors["A"], vectors["B"])\n'
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason is None


@pytest.mark.parametrize(
    "definition",
    [
        'GROUPS = ["A", call()]',
        'GROUPS = [["A"], "B"]',
        "GROUPS = []",
        "GROUPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]",
    ],
)
def test_g5_nonclosed_or_out_of_bound_module_sequences_do_not_open_a_path(
    definition: str,
) -> None:
    source = (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{definition}\n"
        'df = pd.read_csv("data.csv")\n'
        "vectors = {}\n"
        "for level in GROUPS:\n"
        '    vectors[level] = df.loc[df["group"] == level, "value"]\n'
        'result = stats.ttest_ind(vectors["A"], vectors["B"])\n'
        "print(result.pvalue)\n"
    ).encode()
    assert _analyze(source).reason is not None


def test_g6_parse_dates_reader_is_accepted_on_the_authorized_path() -> None:
    result = _analyze(_source(reader='df = pd.read_csv("data.csv", parse_dates=["visit"])'))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.reader_api == "pandas_read_csv_parse_dates_v1"


def test_g6_off_path_parse_dates_reader_participates_in_second_reader_census() -> None:
    source = _source(
        reader=(
            'other = pd.read_csv("other.csv", parse_dates=["visit"])\ndf = pd.read_csv("data.csv")'
        )
    )
    assert _analyze(source).reason == "additional-accepted-reader-present"


@pytest.mark.parametrize(
    "reader",
    [
        'df = pd.read_csv("data.csv", parse_dates=["unit"])',
        'df = pd.read_csv("data.csv", parse_dates=["group"])',
        'df = pd.read_csv("data.csv", parse_dates=["unknown"])',
        'df = pd.read_csv("data.csv", parse_dates=("visit",))',
        'df = pd.read_csv("data.csv", parse_dates=[["visit"]])',
        'df = pd.read_csv("data.csv", parse_dates=["visit"], index_col=0)',
    ],
)
def test_g6_reader_near_misses_abstain(reader: str) -> None:
    assert _analyze(_source(reader=reader)).reason == "authorized-reader-lineage-unavailable"


@pytest.mark.parametrize(
    "conversion",
    [
        'df["visit"] = pd.to_datetime(df["visit"]).dt.date',
        'df["visit"] = df["visit"].astype(str)',
        'df["visit"] = df["visit"].astype(int)',
        'df["visit"] = df["visit"].astype(float)',
    ],
)
def test_g7_same_auxiliary_column_conversion_is_not_a_tracked_mutation(
    conversion: str,
) -> None:
    assert _analyze(_source(before_test=conversion)).reason is None


@pytest.mark.parametrize(
    "conversion",
    [
        'df["unit"] = pd.to_datetime(df["unit"]).dt.date',
        'df["group"] = df["group"].astype(str)',
        'df["value"] = df["value"].astype(float)',
        'df["visit"] = pd.to_datetime(df["group"]).dt.date',
        'df.loc[:, "visit"] = pd.to_datetime(df["visit"]).dt.date',
        'df["visit"] = df["visit"].astype("str")',
    ],
)
def test_g7_protected_or_near_miss_column_conversion_abstains(conversion: str) -> None:
    assert _analyze(_source(before_test=conversion)).reason == "tracked-value-mutation"


def test_g1_subscript_store_defines_resampling_output() -> None:
    source = _source(
        before_test=(
            "draws = [0.0] * 50\n"
            "for i in range(50):\n"
            "    draws[i] = left.mean()\n"
            "spread = np.std(draws)"
        ),
        reader='import numpy as np\ndf = pd.read_csv("data.csv")',
        sink="print(spread)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason == "resampling-inference-sibling-present"


def test_g1_resampling_dominates_earlier_unregistered_component_consumer() -> None:
    source = _source(
        before_test=(
            "opaque = left.to_string(float_format=lambda value: str(value))\n"
            "draws = []\n"
            "for i in range(50):\n"
            "    draws.append(left.mean())\n"
            "spread = np.std(draws)"
        ),
        reader='import numpy as np\ndf = pd.read_csv("data.csv")',
        sink="print(opaque)\nprint(spread)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason == "resampling-inference-sibling-present"


def test_g1_resampling_guard_follows_distinct_helper_edges_to_sink() -> None:
    source = b"""import pandas as pd
import numpy as np
from scipy import stats

N_RESAMPLES = 50

def make_blocks(frame):
    blocks = {
        "A": frame.loc[frame["group"] == "A", "value"],
        "B": frame.loc[frame["group"] == "B", "value"],
    }
    return blocks

def draw(blocks, n_resamples=N_RESAMPLES):
    draws = [0.0] * n_resamples
    for index in range(n_resamples):
        draws[index] = blocks["A"].mean() - blocks["B"].mean()
    return draws

def reduce_draws(draws):
    spread = np.std(draws)
    return spread

def emit(spread):
    print(spread)
    return spread

def main():
    df = pd.read_csv("data.csv")
    blocks = make_blocks(df)
    draws = draw(blocks)
    spread = reduce_draws(draws)
    emitted = emit(spread)
    left = df.loc[df["group"] == "A", "value"]
    right = df.loc[df["group"] == "B", "value"]
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    assert _analyze(source).reason == "resampling-inference-sibling-present"


def test_x4_module_level_transform_is_not_ignored() -> None:
    source = _helper_source(
        "def load():\n    return FRAME\n",
    ).decode()
    source = source.replace(
        'DATA_FILE = "data.csv"\n',
        'DATA_FILE = "data.csv"\nFRAME = pd.read_csv(DATA_FILE)\n',
    )
    assert _analyze(source.encode()).reason == "analysis-scope-ambiguous"


def test_x4_helper_aggregation_under_fresh_name_stays_visible() -> None:
    helper = (
        "def load():\n    return pd.read_csv(DATA_FILE)\n"
        "def pseudobulk(df):\n"
        '    summary = df.groupby("unit").mean()\n'
        "    return summary\n"
    )
    source = _helper_source(
        helper,
        extra_main="    df = pseudobulk(df)\n",
    )
    assert _analyze(source).reason in {
        "tracked-value-mutation",
        "aggregation-on-test-operand-path",
    }


@pytest.mark.parametrize(
    ("return_value", "reason"),
    [
        ("None", "tracked-value-mutation"),
        ("df", "tracked-value-mutation"),
    ],
)
def test_x4_in_place_mutation_never_disappears(return_value: str, reason: str) -> None:
    helper = (
        "def load():\n    return pd.read_csv(DATA_FILE)\n"
        "def mutate(df):\n"
        '    df.drop_duplicates(subset=["unit"], inplace=True)\n'
        f"    return {return_value}\n"
    )
    source = _helper_source(helper, extra_main="    df = mutate(df)\n")
    assert _analyze(source).reason == reason


@pytest.mark.parametrize(
    ("helper", "reason"),
    [
        (
            "def load():\n    pass\n",
            "helper-return-count-unsupported",
        ),
        (
            "def load():\n    return pd.read_csv(DATA_FILE)\n    value = 1\n",
            "helper-return-position-unsupported",
        ),
        (
            "def load():\n    global DATA_FILE\n    return pd.read_csv(DATA_FILE)\n",
            "helper-global-nonlocal-unsupported",
        ),
        (
            "def load():\n    def inner():\n        return DATA_FILE\n    return pd.read_csv(DATA_FILE)\n",
            "helper-closure-or-nested-definition-unsupported",
        ),
        (
            "@decorator\ndef load():\n    return pd.read_csv(DATA_FILE)\n",
            "helper-async-decorator-or-yield-unsupported",
        ),
    ],
)
def test_x4_more_closed_helper_abstention_codes(helper: str, reason: str) -> None:
    assert _analyze(_helper_source(helper)).reason == reason


def test_x4_non_simple_and_nonunique_helper_definitions_abstain() -> None:
    non_simple = _helper_source(
        "def load():\n    return pd.read_csv(DATA_FILE)\n",
        reader="df = namespace.load()",
    )
    assert _analyze(non_simple).reason == "helper-callee-not-simple-name"
    duplicate = _helper_source(
        "def load():\n    return pd.read_csv(DATA_FILE)\n"
        "def load():\n    return pd.read_csv(DATA_FILE)\n"
    )
    assert _analyze(duplicate).reason == "helper-definition-unavailable-or-nonunique"


def test_x4_depth_three_abstains_while_depth_two_is_allowed() -> None:
    depth_two = _helper_source(
        "def inner(path):\n    return pd.read_csv(path)\n"
        "def load(path=DATA_FILE):\n    frame = inner(path)\n    return frame\n"
    )
    assert _analyze(depth_two).reason is None
    depth_three = _helper_source(
        "def inner(path):\n    return pd.read_csv(path)\n"
        "def middle(path):\n    frame = inner(path)\n    return frame\n"
        "def load(path=DATA_FILE):\n    frame = middle(path)\n    return frame\n"
    )
    assert _analyze(depth_three).reason == "helper-inlining-depth-exceeded"


def test_x4_helper_sink_preserves_p_result_requirement() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"def emit(result):\n    print(result.pvalue)\n    return result\n"
        b"def main():\n"
        b'    df = pd.read_csv("data.csv")\n'
        b'    left = df.loc[df["group"] == "A", "value"]\n'
        b'    right = df.loc[df["group"] == "B", "value"]\n'
        b"    result = stats.ttest_ind(left, right)\n"
        b"    saved = emit(result)\n"
        b'if __name__ == "__main__":\n    main()\n'
    )
    assert _analyze(source).reason is None


def test_helper_expansion_is_prose_byte_invariant() -> None:
    template = (
        '"""{module_doc}"""\n'
        "import pandas as pd\n"
        "from scipy import stats\n"
        "def load():\n"
        '    """{helper_doc}"""\n'
        '    return pd.read_csv("data.csv")\n'
        "def main():\n"
        "    df = load()\n"
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        "    result = stats.ttest_ind(left, right)\n"
        '    print("{label}", result.pvalue)\n'
        'if __name__ == "__main__":\n    main()\n'
    )
    variants = (
        {"module_doc": "alpha", "helper_doc": "beta", "label": "gamma"},
        {
            "module_doc": "aggregation pseudoreplication",
            "helper_doc": "mixed model",
            "label": "no averaging",
        },
    )
    results = [_analyze(template.format(**item).encode()) for item in variants]
    assert results[0].facts == results[1].facts
    assert results[0].reason == results[1].reason is None


def test_x5_helper_expansion_is_prose_byte_invariant() -> None:
    template = (
        '"""{module_doc}"""\n'
        "import pandas as pd\n"
        "from scipy import stats\n"
        "def describe(values):\n"
        '    """{helper_doc}"""\n'
        "    mean_value = values.mean()\n"
        '    return {{"mean": mean_value}}\n'
        "def main():\n"
        '    df = pd.read_csv("data.csv")\n'
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        "    description = describe(left)\n"
        '    print("{label}", description["mean"])\n'
        "    result = stats.ttest_ind(left, right)\n"
        "    print(result.pvalue)\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    variants = (
        {"module_doc": "alpha", "helper_doc": "beta", "label": "gamma"},
        {
            "module_doc": "aggregation pseudoreplication",
            "helper_doc": "mixed model no averaging",
            "label": "exploratory primary result",
        },
    )
    results = [_analyze(template.format(**item).encode()) for item in variants]
    assert results[0].facts == results[1].facts
    assert results[0].reason == results[1].reason is None


def test_x4_call_site_reentry_guard_is_reachable_as_an_ir_invariant() -> None:
    tree = dataflow_module._bounded_parse(
        _helper_source("def load():\n    return pd.read_csv(DATA_FILE)\n")
    )
    scope, setup, helpers, reason = dataflow_module._chosen_scope(tree)
    assert reason is None and scope is not None
    resolver, reason = dataflow_module._resolver((*setup, *scope))
    assert reason is None and resolver is not None
    repeated = (scope[0], scope[0], *scope[1:])
    expansion = dataflow_module._expand_relevant_helpers(
        scope=repeated,
        helpers=helpers,
        resolver=resolver,
    )
    assert expansion.reason == "helper-call-site-reentry-unsupported"


@pytest.mark.parametrize(
    ("binding", "guard"),
    [
        (
            "import statsmodels.api as sm",
            'model = sm.MixedLM.from_formula("value ~ group", data=df, groups=df["unit"])',
        ),
        (
            "import statsmodels.api as sm",
            'model = sm.GEE.from_formula("value ~ group", groups="unit", data=df)',
        ),
        (
            "import statsmodels.api as sm",
            'model = sm.MixedLM.any_registered_method(df["value"], groups=df["unit"])',
        ),
        (
            "from statsmodels.regression.mixed_linear_model import MixedLM",
            'model = MixedLM.from_formula("value ~ group", data=df, groups=df["unit"])',
        ),
        (
            "from statsmodels.genmod.generalized_estimating_equations import GEE",
            'model = GEE.from_formula("value ~ group", groups="unit", data=df).fit()',
        ),
    ],
)
def test_b1_dependence_class_root_attribute_chains_always_suppress(
    binding: str, guard: str
) -> None:
    source = (
        _source(after_test=guard)
        .decode()
        .replace("from scipy import stats\n", f"from scipy import stats\n{binding}\n")
    )
    assert _analyze(source.encode()).reason == "dependence-aware-sibling-present"


@pytest.mark.parametrize(
    ("imports", "file_sink"),
    [
        (
            "from pathlib import Path",
            'Path("out.txt").write_text(str(custom_model(df)), encoding="utf-8")',
        ),
        (
            "",
            'with open("out.txt", "w", encoding="utf-8") as handle:\n'
            "    handle.write(str(custom_model(df)))",
        ),
        ("", 'custom_model(df).to_csv("out.csv")'),
        ("import numpy as np", 'np.savetxt("out.csv", custom_model(df))'),
        (
            "import json",
            'with open("out.json", "w", encoding="utf-8") as handle:\n'
            "    json.dump(custom_model(df), handle)",
        ),
    ],
)
def test_b2_unregistered_component_call_reaching_every_shared_sink_abstains(
    imports: str, file_sink: str
) -> None:
    source = (
        _source(after_test=file_sink)
        .decode()
        .replace(
            "from scipy import stats\n",
            f"from scipy import stats\n{imports}\n" if imports else "from scipy import stats\n",
        )
    )
    assert _analyze(source.encode()).reason == "unregistered-component-consumer"


@pytest.mark.parametrize(
    ("imports", "sink", "sink_kind"),
    [
        ("", "print(result.pvalue)", "builtin_print"),
        (
            "from pathlib import Path",
            'Path("out.txt").write_text(str(result.pvalue), encoding="utf-8")',
            "path_write_text_utf8",
        ),
        (
            "",
            'with open("out.txt", "wt", encoding="utf-8", newline="") as handle:\n'
            "    handle.write(str(result.pvalue))",
            "bounded_text_handle_write",
        ),
    ],
)
def test_shared_sink_registry_drives_p_result_output(
    imports: str, sink: str, sink_kind: str
) -> None:
    source = (
        _source(sink=sink)
        .decode()
        .replace(
            "from scipy import stats\n",
            f"from scipy import stats\n{imports}\n" if imports else "from scipy import stats\n",
        )
    )
    result = _analyze(source.encode())
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.output_sink_kinds == (sink_kind,)


def test_b3_descriptive_loop_cannot_rebind_any_tracked_backward_slice_name() -> None:
    loop = 'for df, label in ((left, "A"), (right, "B")):\n    print(label, df.mean())'
    assert _analyze(_source(before_test=loop)).reason == "loop-target-aliases-tracked"


@pytest.mark.parametrize(
    "definition",
    ["def print(*args):\n    pass", "class open:\n    pass", "def len(value):\n    return 1"],
)
def test_b3_function_and_class_builtin_shadowing_abstains(definition: str) -> None:
    source = f"{definition}\n{_source().decode()}".encode()
    assert _analyze(source).reason == "api-resolution-ambiguous"


@pytest.mark.parametrize(
    "statement",
    [
        "global external_state",
        "def helper():\n    nonlocal external_state",
    ],
)
def test_b5_global_and_nonlocal_anywhere_abstain(statement: str) -> None:
    source = f"{statement}\n{_source().decode()}".encode()
    assert _analyze(source).reason == "unsupported-control-flow-on-path"


def test_b5_import_pathlib_path_is_exactly_resolved_like_from_import() -> None:
    module_form = _source(reader='df = pathlib.Path("data.csv") and pd.read_csv("data.csv")')
    module_form = module_form.decode().replace(
        "import pandas as pd\n", "import pandas as pd\nimport pathlib\n"
    )
    from_form = _source(reader='df = Path("data.csv") and pd.read_csv("data.csv")')
    from_form = from_form.decode().replace(
        "import pandas as pd\n", "import pandas as pd\nfrom pathlib import Path\n"
    )
    # The path object must occupy the reader argument, not merely coexist in a boolean expression.
    module_form = module_form.replace(
        'df = pathlib.Path("data.csv") and pd.read_csv("data.csv")',
        'df = pd.read_csv(pathlib.Path("data.csv"))',
    )
    from_form = from_form.replace(
        'df = Path("data.csv") and pd.read_csv("data.csv")',
        'df = pd.read_csv(Path("data.csv"))',
    )
    assert _analyze(module_form.encode()).reason is None
    assert _analyze(from_form.encode()).reason is None


def test_b5_module_level_computed_path_constant_abstains() -> None:
    source = (
        "import pandas as pd\n"
        "from pathlib import Path\n"
        "from scipy import stats\n"
        'DATA = Path("data.csv")\n'
        "def main() -> None:\n"
        "    df = pd.read_csv(DATA)\n"
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        "    result = stats.ttest_ind(left, right)\n"
        "    print(result.pvalue)\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    assert _analyze(source.encode()).reason == "analysis-scope-ambiguous"


@pytest.mark.parametrize("alias_count", [13, 14])
def test_b4_p_result_to_sink_definition_ceiling(alias_count: int) -> None:
    aliases = ["p0 = result.pvalue"]
    aliases.extend(f"p{index} = p{index - 1}" for index in range(1, alias_count + 1))
    source = _source(after_test="\n".join(aliases), sink=f"print(p{alias_count})")
    result = _analyze(source)
    if alias_count == 13:
        assert result.reason is None
        assert result.facts is not None
        assert result.facts.dataflow_max_definition_nodes == 16
    else:
        assert result.reason == "dataflow-definition-ceiling-exceeded"


@pytest.mark.parametrize("alias_count", [13, 14])
def test_b4_reader_component_sibling_definition_ceiling(alias_count: int) -> None:
    aliases = ["other0 = custom_model(df)"]
    aliases.extend(f"other{index} = other{index - 1}" for index in range(1, alias_count + 1))
    source = _source(
        after_test="\n".join(aliases), sink=f"print(result.pvalue, other{alias_count})"
    )
    expected = (
        "unregistered-component-consumer"
        if alias_count == 13
        else "dataflow-definition-ceiling-exceeded"
    )
    assert _analyze(source).reason == expected


@pytest.mark.parametrize(
    ("imports", "reader_prefix", "test_call"),
    [
        (
            "import pandas\nfrom scipy import stats",
            "pandas.read_csv",
            "stats.ttest_ind",
        ),
        (
            "import pandas as frame_api\nimport scipy.stats as test_api",
            "frame_api.read_csv",
            "test_api.ttest_ind",
        ),
        (
            "import pandas as pd\nimport scipy",
            "pd.read_csv",
            "scipy.stats.ttest_ind",
        ),
        (
            "import pandas as pd\nfrom scipy.stats import ttest_ind",
            "pd.read_csv",
            "ttest_ind",
        ),
        (
            "import pandas as pd\nfrom scipy.stats import ttest_ind as two_sample",
            "pd.read_csv",
            "two_sample",
        ),
    ],
)
def test_import_and_callable_positive_allowlist(
    imports: str, reader_prefix: str, test_call: str
) -> None:
    source = (
        f"{imports}\n"
        f'df = {reader_prefix}("data.csv")\n'
        'left = df.loc[df["group"] == "A", "value"]\n'
        'right = df.loc[df["group"] == "B", "value"]\n'
        f"result = {test_call}(left, right)\n"
        "print(result.pvalue)\n"
    )
    assert _analyze(source.encode()).reason is None


@pytest.mark.parametrize(
    "source_prefix",
    [
        "from scipy.stats import *",
        "from .scipy import stats",
        'stats = __import__("scipy.stats")',
        "import importlib",
        "from importlib import import_module",
        "from scipy import stats\nstats = object()",
        "from scipy import stats\nprint = object()",
    ],
)
def test_import_and_callable_negative_allowlist(source_prefix: str) -> None:
    source = _source().decode().replace("from scipy import stats", source_prefix)
    assert _analyze(source.encode()).facts is None


@pytest.mark.parametrize(
    ("imports", "path"),
    [
        ("", '"data.csv"'),
        ("", "DATA"),
        ("from pathlib import Path", 'Path("data.csv")'),
        ("from pathlib import Path", 'Path("data") / "nested.csv"'),
        ("import pathlib", 'pathlib.Path("data") / "nested.csv"'),
    ],
)
def test_static_path_positive_allowlist(imports: str, path: str) -> None:
    authorized = "data/nested.csv" if "nested" in path else "data.csv"
    constant = 'DATA = "data.csv"\n' if path == "DATA" else ""
    source = (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{imports}\n"
        f"{constant}"
        f"df = pd.read_csv({path})\n"
        'left = df.loc[df["group"] == "A", "value"]\n'
        'right = df.loc[df["group"] == "B", "value"]\n'
        "result = stats.ttest_ind(left, right)\n"
        "print(result.pvalue)\n"
    )
    result = analyze_code_csv_dataflow(
        source.encode(),
        authorized_path=authorized,
        unit_column="unit",
        group_column="group",
        csv_header=_HEADER,
        group_values=_GROUPS,
    )
    assert result.reason is None


@pytest.mark.parametrize(
    "path_expression",
    [
        '"DATA.CSV"',
        '"../data.csv"',
        '"/data.csv"',
        '"data" + ".csv"',
        'f"{prefix}.csv"',
        'os.path.join("data", "file.csv")',
    ],
)
def test_static_path_negative_allowlist(path_expression: str) -> None:
    source = (
        "import pandas as pd\n"
        "import os\n"
        "from pathlib import Path\n"
        "from scipy import stats\n"
        'prefix = "data"\n'
        f"df = pd.read_csv({path_expression})\n"
        'left = df.loc[df["group"] == "A", "value"]\n'
        'right = df.loc[df["group"] == "B", "value"]\n'
        "result = stats.ttest_ind(left, right)\n"
        "print(result.pvalue)\n"
    )
    assert _analyze(source.encode()).reason == "authorized-reader-lineage-unavailable"


@pytest.mark.parametrize(
    "reader",
    [
        'df = pd.read_csv("data.csv", header=0)',
        'df = pd.read_csv("data.csv", "extra")',
        'df = pd.read_table("data.csv")',
        "df = pd.read_csv(dynamic_path)",
    ],
)
def test_pandas_reader_negative_matrix(reader: str) -> None:
    assert _analyze(_source(reader=reader)).facts is None


@pytest.mark.parametrize(
    "mutation",
    [
        'delimiter=";", names=True, dtype=None, encoding="utf-8"',
        'delimiter=",", names=False, dtype=None, encoding="utf-8"',
        'delimiter=",", names=True, dtype=str, encoding="utf-8"',
        'delimiter=",", names=True, dtype=None, encoding="ascii"',
        'delimiter=",", names=True, dtype=None',
    ],
)
def test_numpy_reader_keyword_negative_matrix(mutation: str) -> None:
    source = (
        "import numpy as np\n"
        "from scipy import stats\n"
        f'df = np.genfromtxt("data.csv", {mutation})\n'
        'left = df[df["group"] == "A"]["value"]\n'
        'right = df[df["group"] == "B"]["value"]\n'
        "result = stats.ttest_ind(left, right)\n"
        "print(result.pvalue)\n"
    )
    assert _analyze(source.encode()).reason == "authorized-reader-lineage-unavailable"


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            'left = df.loc[df["group"] != "A", "value"]',
            'right = df.loc[df["group"] == "B", "value"]',
        ),
        (
            'left = df.loc[df["other"] == "A", "value"]',
            'right = df.loc[df["other"] == "B", "value"]',
        ),
        (
            'left = df.loc[df["group"] == "A", "other"]',
            'right = df.loc[df["group"] == "B", "other"]',
        ),
        (
            'left = df.query("group != \'A\'")["value"]',
            'right = df.query("group == \'B\'")["value"]',
        ),
        (
            'left = df.iloc[df["group"] == "A", 3]',
            'right = df.iloc[df["group"] == "B", 3]',
        ),
        (
            'left = df.loc[df["group"] == "A", "value"].dropna()',
            'right = df.loc[df["group"] == "B", "value"].dropna()',
        ),
    ],
)
def test_selection_negative_matrix(left: str, right: str) -> None:
    assert _analyze(_source(left=left, right=right)).facts is None


@pytest.mark.parametrize(
    "method",
    [
        "agg",
        "aggregate",
        "mean",
        "median",
        "sum",
        "first",
        "last",
        "min",
        "max",
        "count",
        "size",
        "nunique",
        "prod",
        "std",
        "var",
        "sem",
        "quantile",
    ],
)
def test_every_groupby_reducer_is_aggregation_on_operand_path(method: str) -> None:
    call = f'summary = df.groupby("unit").{method}()'
    source = _source(
        left=f'{call}\nleft = summary.loc[summary["group"] == "A", "value"]',
        right='right = summary.loc[summary["group"] == "B", "value"]',
    )
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    "api",
    [
        "mean",
        "nanmean",
        "median",
        "nanmedian",
        "sum",
        "nansum",
        "average",
        "min",
        "nanmin",
        "max",
        "nanmax",
        "std",
        "nanstd",
        "var",
        "nanvar",
    ],
)
def test_every_numpy_reducer_is_aggregation_on_operand_path(api: str) -> None:
    source = (
        _source(
            left=(f'summary = np.{api}(df)\nleft = summary.loc[summary["group"] == "A", "value"]'),
            right='right = summary.loc[summary["group"] == "B", "value"]',
        )
        .decode()
        .replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n")
    )
    assert _analyze(source.encode()).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    "test",
    [
        "result = stats.ttest_ind(left, right, nan_policy='omit')",
        "result = stats.ttest_ind(left, right, equal_var=flag)",
        "result = stats.ttest_ind(left, right, equal_var=False, axis=0)",
        "result = stats.mannwhitneyu(left, right, alternative='invalid')",
        "result = stats.mannwhitneyu(left, right, method='exact')",
        "result = stats.ttest_rel(left, right)",
        "result = stats.f_oneway(left, right)",
    ],
)
def test_registered_test_negative_matrix(test: str) -> None:
    assert _analyze(_source(test=test)).facts is None


@pytest.mark.parametrize(
    "sink",
    [
        "print(result.pvalue)",
        "print(result[1])",
        "print(str(result.pvalue))",
        "print(float(result.pvalue))",
        "print(round(result.pvalue, 3))",
        'print(f"{result.pvalue}")',
        'print("{}".format(result.pvalue))',
    ],
)
def test_p_result_payload_wrapper_positive_matrix(sink: str) -> None:
    assert _analyze(_source(sink=sink)).reason is None


@pytest.mark.parametrize(
    "sink",
    [
        "print(result.statistic)",
        "print(result[0])",
        "print(result.pvalue + 1)",
        "logger.info(result.pvalue)",
        "print(result.pvalue, file=handle)",
        "print(*[result.pvalue])",
        "print(round(result.pvalue, digits))",
    ],
)
def test_p_result_payload_wrapper_negative_matrix(sink: str) -> None:
    assert _analyze(_source(sink=sink)).facts is None


def test_prose_mutations_leave_dataflow_observation_byte_identical() -> None:
    template = (
        '"""{doc}"""\n'
        "# {comment}\n"
        '"{standalone}"\n'
        "import pandas as pd\n"
        "from scipy import stats\n"
        'df = pd.read_csv("data.csv")\n'
        'left = df.loc[df["group"] == "A", "value"]\n'
        'right = df.loc[df["group"] == "B", "value"]\n'
        "result = stats.ttest_ind(left, right)\n"
        'print("{label}", result.pvalue)\n'
    )
    variants = [
        {"doc": "AAAAAAAA", "comment": "BBBBBBBB", "standalone": "CCCCCCCC", "label": "DDDDDDDD"},
        {"doc": "averaged", "comment": "independ", "standalone": "primary!", "label": "explorer"},
        {"doc": "mixedmod", "comment": "no-avera", "standalone": "suppress!", "label": "row-wise"},
    ]
    facts = [_analyze(template.format(**variant).encode()).facts for variant in variants]
    assert all(item is not None for item in facts)
    assert facts[0] == facts[1] == facts[2]


@pytest.mark.parametrize(
    "method",
    [
        "mean",
        "median",
        "sum",
        "min",
        "max",
        "count",
        "nunique",
        "prod",
        "std",
        "var",
        "sem",
        "quantile",
        "pivot_table",
    ],
)
def test_every_frame_reducer_is_aggregation_on_operand_path(method: str) -> None:
    source = _source(
        left=(f'summary = df.{method}()\nleft = summary.loc[summary["group"] == "A", "value"]'),
        right='right = summary.loc[summary["group"] == "B", "value"]',
    )
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    "api",
    ["mean", "fmean", "median", "median_low", "median_high"],
)
def test_every_statistics_reducer_is_aggregation_on_operand_path(api: str) -> None:
    source = _source(
        left=(
            f'summary = descriptive.{api}(df)\nleft = summary.loc[summary["group"] == "A", "value"]'
        ),
        right='right = summary.loc[summary["group"] == "B", "value"]',
    ).decode()
    source = source.replace(
        "import pandas as pd\n", "import pandas as pd\nimport statistics as descriptive\n"
    )
    assert _analyze(source.encode()).reason == "aggregation-on-test-operand-path"


def test_builtin_sum_is_aggregation_on_operand_path() -> None:
    source = _source(
        left=('summary = sum(df)\nleft = summary.loc[summary["group"] == "A", "value"]'),
        right='right = summary.loc[summary["group"] == "B", "value"]',
    )
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


@pytest.mark.parametrize(
    "transform",
    [
        'summary = df.pivot(index="unit", columns="group", values="value")',
        'summary = df.resample("D")',
        "summary = df.rolling(2).mean()",
        "summary = df.expanding(2).mean()",
    ],
)
def test_registry_asymmetry_transforms_abstain_not_pass_through(transform: str) -> None:
    source = _source(
        left=f'{transform}\nleft = summary.loc[summary["group"] == "A", "value"]',
        right='right = summary.loc[summary["group"] == "B", "value"]',
    )
    assert _analyze(source).facts is None


@pytest.mark.parametrize(
    ("imports", "guard"),
    [
        ("", "paired = stats.ttest_rel(left, right)"),
        ("", "paired = stats.wilcoxon(left, right)"),
        (
            "import statsmodels.formula.api as smf",
            'model = smf.mixedlm("value ~ group", data=df, groups=df["unit"])',
        ),
        (
            "import statsmodels.api as sm",
            'model = sm.MixedLM(df["value"], df[["group"]], groups=df["unit"])',
        ),
        (
            "import statsmodels.api as sm",
            'model = sm.GEE(df["value"], df[["group"]], groups=df["unit"])',
        ),
    ],
)
def test_dependence_guard_api_matrix(imports: str, guard: str) -> None:
    source = _source(after_test=guard).decode()
    if imports:
        source = source.replace(
            "from scipy import stats\n", f"from scipy import stats\n{imports}\n"
        )
    assert _analyze(source.encode()).reason == "dependence-aware-sibling-present"


@pytest.mark.parametrize("alternative", ["two-sided", "less", "greater"])
def test_all_mannwhitney_alternatives_are_registered(alternative: str) -> None:
    test = f'result = stats.mannwhitneyu(left, right, alternative="{alternative}")'
    result = _analyze(_source(test=test))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.procedure_id == "scipy.stats.mannwhitneyu"


@pytest.mark.parametrize(
    "expression",
    [
        "values.mean()",
        "values.std()",
        "values.std(ddof=1)",
        "values.median()",
        "values.min()",
        "values.max()",
        "values.count()",
        "values.sum()",
        "len(values)",
        "sum(values)",
        "min(values)",
        "max(values)",
        "round(values.mean())",
        "round(values.mean(), 2)",
    ],
)
def test_every_descriptive_loop_reduction_flows_only_to_print(expression: str) -> None:
    loop = f'for label, values in (("A", left), ("B", right)):\n    print(label, {expression})'
    result = _analyze(_source(before_test=loop))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.descriptive_loop_count == 1


@pytest.mark.parametrize(
    ("expression", "expected_reason"),
    [
        ("values.var()", None),
        ("values.std(ddof=0)", None),
        ("round(values.mean(), digits)", "unregistered-component-consumer"),
        ("custom(values)", "unregistered-component-consumer"),
    ],
)
def test_v2_loop_calls_follow_the_closed_readonly_list(
    expression: str, expected_reason: str | None
) -> None:
    loop = f'for label, values in (("A", left), ("B", right)):\n    print(label, {expression})'
    assert _analyze(_source(before_test=loop)).reason == expected_reason


@pytest.mark.parametrize("annotation", ["", " -> None"])
def test_exact_main_scope_forms_are_positive(annotation: str) -> None:
    source = (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"def main(){annotation}:\n"
        '    df = pd.read_csv("data.csv")\n'
        '    left = df.loc[df["group"] == "A", "value"]\n'
        '    right = df.loc[df["group"] == "B", "value"]\n'
        "    result = stats.ttest_ind(left, right)\n"
        "    print(result.pvalue)\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    assert _analyze(source.encode()).reason is None


@pytest.mark.parametrize(
    "main_line",
    [
        "def main(value):",
        "async def main():",
        "@decorator\ndef main():",
    ],
)
def test_nonexact_main_scope_forms_abstain(main_line: str) -> None:
    source = (
        "import pandas as pd\n"
        "from scipy import stats\n"
        f"{main_line}\n"
        "    pass\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    assert _analyze(source.encode()).reason == "analysis-scope-ambiguous"


@pytest.mark.parametrize(
    "sink",
    [
        'Path("../out.txt").write_text(str(result.pvalue), encoding="utf-8")',
        'Path("out.txt").write_text(str(result.pvalue), encoding="ascii")',
        'Path("out.txt").write_text(str(result.pvalue))',
        'with open("out.txt", "a", encoding="utf-8") as handle:\n'
        "    handle.write(str(result.pvalue))",
        'with open("out.txt", "w") as handle:\n    handle.write(str(result.pvalue))',
    ],
)
def test_file_sink_negative_matrix(sink: str) -> None:
    source = (
        _source(sink=sink)
        .decode()
        .replace("from scipy import stats\n", "from scipy import stats\nfrom pathlib import Path\n")
    )
    assert _analyze(source.encode()).facts is None


def test_b2_assigned_unregistered_result_reaches_file_sink() -> None:
    source = _source(
        after_test="other = custom_model(df)",
        sink='Path("out.txt").write_text(str(other), encoding="utf-8")',
    ).decode()
    source = source.replace(
        "from scipy import stats\n", "from scipy import stats\nfrom pathlib import Path\n"
    )
    assert _analyze(source.encode()).reason == "unregistered-component-consumer"


@pytest.mark.parametrize(
    "csv_source",
    [
        (
            "import csv\n"
            "from scipy import stats\n"
            'with open("data.csv", "r", encoding="utf-8", newline="") as handle:\n'
            "    df = list(csv.DictReader(handle))\n"
            'left = [float(row["value"]) for row in df if row["group"] == "A"]\n'
            'right = [float(row["value"]) for row in df if row["group"] == "B"]\n'
            "result = stats.ttest_ind(left, right)\n"
            "print(result.pvalue)\n"
        ),
        (
            "import csv\n"
            "from scipy import stats\n"
            'buckets = {"A": [], "B": []}\n'
            'with open("data.csv", "r", encoding="utf-8", newline="") as handle:\n'
            "    for row in csv.DictReader(handle):\n"
            '        buckets[row["group"]].append(float(row["value"]))\n'
            'left = buckets["A"]\n'
            'right = buckets["B"]\n'
            "result = stats.ttest_ind(left, right)\n"
            "print(result.pvalue)\n"
        ),
    ],
)
def test_deliberately_unimplemented_dictreader_rows_abstain(csv_source: str) -> None:
    assert _analyze(csv_source.encode()).facts is None


@pytest.mark.parametrize(
    "drop_call",
    [
        'df.drop_duplicates(subset="unit")',
        'df.drop_duplicates(subset=["unit"])',
        'df.drop_duplicates(subset="visit")',
        "df.drop_duplicates()",
    ],
)
def test_drop_duplicates_shapes_never_pass_through(drop_call: str) -> None:
    source = _source(
        left=(
            f"deduplicated = {drop_call}\n"
            'left = deduplicated.loc[deduplicated["group"] == "A", "value"]'
        ),
        right='right = deduplicated.loc[deduplicated["group"] == "B", "value"]',
    )
    assert _analyze(source).facts is None


def test_deliberately_unimplemented_per_unit_reducer_loop_abstains() -> None:
    source = _source(
        left=(
            "buckets = {}\n"
            "for row in df:\n"
            '    buckets.setdefault(row["unit"], []).append(row["value"])\n'
            "per_unit = [sum(values) / len(values) for values in buckets.values()]\n"
            "left = per_unit"
        ),
        right="right = per_unit",
    )
    assert _analyze(source).facts is None


@pytest.mark.parametrize(
    "expression",
    [
        "np.sqrt(left, output)",
        "np.mean(left, 0, output)",
        "np.percentile(left, 50, None, output, True)",
        "np.median(left, None, output, True)",
        "np.percentile(left, 50, overwrite_input=True)",
        "np.nanmedian(left, overwrite_input=True)",
    ],
)
def test_v2_numpy_positional_out_and_overwrite_input_abstain(expression: str) -> None:
    source = (
        _source(before_test=f"description = {expression}")
        .decode()
        .replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n")
    )
    result = _analyze(source.encode())
    assert result.facts is None
    assert result.reason in {"admission-call-off-list", "unregistered-component-consumer"}


@pytest.mark.parametrize(
    "expression",
    [
        "np.median(left, overwrite_input=True)",
        "np.nanmedian(left, None, True)",
        "np.mean(left, out=buf)",
        "np.max(left, None, buf)",
        "np.mean(left, where=True)",
    ],
)
def test_g1_invalid_numpy_reducers_abstain_after_the_test(expression: str) -> None:
    source = (
        _source(after_test=f"buf = left\ndescription = {expression}\nprint(description)")
        .decode()
        .replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n")
    )
    assert _analyze(source.encode()).reason == "admission-call-off-list"


def test_g6_valid_numpy_mean_is_readonly_before_the_test() -> None:
    source = (
        _source(before_test="description = np.mean(left)", sink="print(description, result.pvalue)")
        .decode()
        .replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n")
    )
    assert _analyze(source.encode()).reason is None


@pytest.mark.parametrize("terminal", ["mean", "sum", "describe"])
def test_g2_inline_projected_groupby_terminals_never_receive_r1_admission(
    terminal: str,
) -> None:
    source = _source(before_test=f'summary = df.groupby("unit")["value"].{terminal}()')
    assert _analyze(source).reason == "admission-call-off-list"


@pytest.mark.parametrize(
    "mutation",
    [
        'df.loc[0, "value"] = 0',
        "df.iloc[0, 3] = 0",
        'df.at[0, "value"] = 0',
        'df["value"] = 0',
    ],
)
def test_g3_post_test_tracked_frame_stores_abstain(mutation: str) -> None:
    assert _analyze(_source(after_test=mutation)).reason == "tracked-value-mutation"


@pytest.mark.parametrize(
    "mutation",
    [
        "df.reset_index(inplace=True)",
        'df.sort_values("value", inplace=True)',
        'df.drop_duplicates(subset=["unit"], inplace=True)',
    ],
)
def test_g3_post_test_inplace_mutations_abstain(mutation: str) -> None:
    assert _analyze(_source(after_test=mutation)).reason == "tracked-value-mutation"


def test_g4_flat_script_helper_calls_remain_a_coverage_limit() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"def select_group(frame, label):\n"
        b'    return frame.loc[frame["group"] == label, "value"]\n'
        b'df = pd.read_csv("data.csv")\n'
        b'left = select_group(df, "A")\n'
        b'right = select_group(df, "B")\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "unregistered-component-consumer"


@pytest.mark.parametrize(
    "expression",
    [
        "sorted(left, key=custom)",
        "min(left, key=custom)",
        "max(left, key=custom)",
    ],
)
def test_v2_key_callbacks_are_not_readonly(expression: str) -> None:
    assert _analyze(_source(before_test=f"description = {expression}")).reason == (
        "unregistered-component-consumer"
    )


@pytest.mark.parametrize(
    "name",
    [
        "print",
        "len",
        "int",
        "float",
        "str",
        "round",
        "abs",
        "min",
        "max",
        "sum",
        "sorted",
        "range",
        "enumerate",
        "zip",
        "set",
        "list",
        "dict",
        "tuple",
        "bool",
        "isinstance",
        "format",
        "any",
        "all",
        "repr",
        "divmod",
    ],
)
def test_v2_every_registered_builtin_requires_unshadowed_identity(name: str) -> None:
    source = _source(before_test=f"{name} = custom")
    assert _analyze(source).reason == "api-resolution-ambiguous"


@pytest.mark.parametrize(
    "target",
    [
        'df.loc[0, "value"]',
        "df.iloc[0, 3]",
        'df.at[0, "value"]',
    ],
)
def test_v2_label_and_position_stores_are_tracked_mutations(target: str) -> None:
    assert _analyze(_source(before_test=f"{target} = 0")).reason == "tracked-value-mutation"


@pytest.mark.parametrize(
    "call",
    [
        "df.reset_index(inplace=True)",
        'df.sort_values("value", inplace=True)',
        'df.drop_duplicates(subset=["unit"], inplace=True)',
    ],
)
def test_v2_inplace_methods_are_may_write_component_consumers(call: str) -> None:
    assert _analyze(_source(before_test=call)).reason == "tracked-value-mutation"


def test_v2_try_except_reader_fallback_is_a_second_reader() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b"try:\n"
        b'    df = pd.read_csv("data.csv")\n'
        b"except ValueError:\n"
        b'    df = pd.read_csv("data.csv")\n'
        b'left = df.loc[df["group"] == "A", "value"]\n'
        b'right = df.loc[df["group"] == "B", "value"]\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "additional-accepted-reader-present"


def test_v2_with_open_reader_handle_is_not_an_authorized_reader_path() -> None:
    source = (
        b"import pandas as pd\n"
        b"from scipy import stats\n"
        b'with open("data.csv", "r", encoding="utf-8") as handle:\n'
        b"    df = pd.read_csv(handle)\n"
        b'left = df.loc[df["group"] == "A", "value"]\n'
        b'right = df.loc[df["group"] == "B", "value"]\n'
        b"result = stats.ttest_ind(left, right)\n"
        b"print(result.pvalue)\n"
    )
    assert _analyze(source).reason == "authorized-reader-lineage-unavailable"


@pytest.mark.parametrize(
    ("test", "sink"),
    [
        ("result = stats.ttest_ind(left, right)", "print(result.pvalue)"),
        ("", "print(stats.ttest_ind(left, right).pvalue)"),
        (
            'payload = {"p": stats.ttest_ind(left, right).pvalue}',
            'print(payload["p"])',
        ),
    ],
)
def test_v2_registered_test_and_p_result_survive_nested_output_shapes(test: str, sink: str) -> None:
    assert _analyze(_source(test=test, sink=sink)).reason is None


def test_v2_comprehension_over_protected_selection_abstains() -> None:
    source = _source(before_test="description = [value for value in left]")
    assert _analyze(source).reason == "admission-slice-reaches-operand"


def test_v2_comprehension_over_columns_is_readonly() -> None:
    source = _source(
        before_test="description = [str(column) for column in df.columns]",
        sink="print(description)\nprint(result.pvalue)",
    )
    assert _analyze(source).reason is None


def test_v2_partial_wrapped_test_is_not_a_registered_test() -> None:
    source = (
        _source(
            test="compare = partial(stats.ttest_ind)\nresult = compare(left, right)",
        )
        .decode()
        .replace(
            "from scipy import stats\n", "from scipy import stats\nfrom functools import partial\n"
        )
    )
    assert _analyze(source.encode()).facts is None


def test_v2_groupby_value_laundered_through_loop_into_test_abstains() -> None:
    source = _source(
        before_test=(
            'summary = df.groupby("group")["value"].mean()\n'
            'for label, values in (("A", summary), ("B", summary)):\n'
            '    if label == "A":\n'
            "        left = values\n"
        )
    )
    assert _analyze(source).facts is None


def test_v2_pure_allowlist_bootstrap_beside_raw_test_suppresses() -> None:
    source = (
        _source(
            before_test=(
                "replicates = [float(left.iloc[index % len(left)]) - "
                "float(right.iloc[index % len(right)]) for index in range(50)]\n"
                "lower = np.percentile(replicates, 2.5)\n"
                "print(lower)"
            )
        )
        .decode()
        .replace("import pandas as pd\n", "import pandas as pd\nimport numpy as np\n")
    )
    assert _analyze(source.encode()).reason == "resampling-inference-sibling-present"


def test_v2_raw_test_only_boundary_remains_a_contract_conflict_candidate() -> None:
    source = _source(sink='print("illustrative only", result.pvalue)')
    assert _analyze(source).reason is None


def test_v2_break_in_control_flow_body_abstains() -> None:
    source = _source(before_test="for value in (1, 2):\n    break")
    assert _analyze(source).reason == "control-flow-body-unadmitted"


def test_v22_helper_expands_inside_contract_domain_loop_and_reconstructs_operands() -> None:
    source = b"""import pandas as pd
from scipy import stats

GROUPS = ("A", "B")

def select_group(frame, level):
    selected = frame.loc[frame["group"] == level, "value"]
    return selected

def main():
    df = pd.read_csv("data.csv")
    summary = {}
    for level in GROUPS:
        values = select_group(df, level)
        summary[level] = values
    left = summary["A"]
    right = summary["B"]
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.group_values == _GROUPS


def test_v22_depth_two_helper_expansion_gets_fresh_names_per_contract_binding() -> None:
    source = b"""import pandas as pd
from scipy import stats

GROUPS = ("A", "B")

def inner(frame, level):
    return frame.loc[frame["group"] == level, "value"]

def outer(frame, level):
    selected = inner(frame, level)
    return selected

def main():
    df = pd.read_csv("data.csv")
    summary = {}
    for level in GROUPS:
        values = outer(df, level)
        summary[level] = values
    left = summary["A"]
    right = summary["B"]
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None


def test_v22_helper_expands_as_loop_iterable_receiver_without_hiding_aggregation() -> None:
    source = b"""import pandas as pd
from scipy import stats

def means_by_visit(frame):
    table = frame.groupby("visit")["value"].mean()
    return table

def main():
    df = pd.read_csv("data.csv")
    left = df.loc[df["group"] == "A", "value"]
    right = df.loc[df["group"] == "B", "value"]
    for visit, average in means_by_visit(df).items():
        print(visit, average)
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    result = _analyze(source)
    assert result.reason is None
    assert result.facts is not None


def test_v22_loop_body_helper_aggregation_cannot_be_laundered_into_test() -> None:
    source = b"""import pandas as pd
from scipy import stats

GROUPS = ("A", "B")

def aggregate_group(frame, level):
    selected = frame.loc[frame["group"] == level, "value"]
    reduced = selected.groupby(frame["unit"]).sum()
    return reduced

def main():
    df = pd.read_csv("data.csv")
    summary = {}
    for level in GROUPS:
        values = aggregate_group(df, level)
        summary[level] = values
    left = summary["A"]
    right = summary["B"]
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    assert _analyze(source).reason == "aggregation-on-test-operand-path"


def test_v22_non_contract_loop_label_never_resolves_partially() -> None:
    source = b"""import pandas as pd
from scipy import stats

GROUPS = ("A", "outside")
df = pd.read_csv("data.csv")
summary = {}
for level in GROUPS:
    values = df.loc[df["group"] == level, "value"]
    summary[level] = values
left = summary["A"]
right = summary["B"]
result = stats.ttest_ind(left, right)
print(result.pvalue)
"""
    assert _analyze(source).reason == "two-group-row-selection-unavailable"


def test_v22_mixed_dict_reconstruction_abstains_before_any_candidate() -> None:
    source = b"""import pandas as pd
from scipy import stats

GROUPS = ("A", "B")
df = pd.read_csv("data.csv")
summary = {}
for level in GROUPS:
    values = df.loc[df["group"] == level, "value"]
    if level == "B":
        values = values.groupby(df["unit"]).mean()
    summary[level] = values
left = summary["A"]
right = summary["B"]
result = stats.ttest_ind(left, right)
print(result.pvalue)
"""
    assert _analyze(source).reason == "two-group-row-selection-unavailable"


def test_v22_helper_in_loop_keeps_dependence_aware_sibling_visible() -> None:
    source = b"""import pandas as pd
from scipy import stats
import statsmodels.api as sm

GROUPS = ("A", "B")

def select_group(frame, level):
    model = sm.MixedLM.from_formula("value ~ group", groups="unit", data=frame)
    return frame.loc[frame["group"] == level, "value"]

def main():
    df = pd.read_csv("data.csv")
    summary = {}
    for level in GROUPS:
        values = select_group(df, level)
        summary[level] = values
    left = summary["A"]
    right = summary["B"]
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
"""
    assert _analyze(source).reason == "dependence-aware-sibling-present"


def test_v22_loop_target_that_aliases_tracked_frame_still_abstains() -> None:
    source = _source(
        before_test='for df in ("A", "B"):\n    print(df)',
    )
    assert _analyze(source).reason == "loop-target-aliases-tracked"


def test_v22_literal_container_assignment_does_not_unpack_groupby_pair() -> None:
    groupby_source = _source(
        before_test='summary = {}\nfor level, values in df.groupby("group"):\n    summary[level] = values',
    )
    assert _analyze(groupby_source).reason is not None


def _v22_reconstruction_source(
    *,
    setup: str = "",
    iterable: str = '("A", "B")',
    body_before_store: str = "",
    after_loop: str = "",
    left: str = 'summary["A"]',
    right: str = 'summary["B"]',
    loop_else: str = "",
) -> bytes:
    return f"""import pandas as pd
from scipy import stats
{setup}
df = pd.read_csv("data.csv")
summary = {{}}
for level in {iterable}:
    values = df.loc[df["group"] == level, "value"]
{body_before_store}    summary[level] = values
{loop_else}{after_loop}
left = {left}
right = {right}
result = stats.ttest_ind(left, right)
print(result.pvalue)
""".encode()


@pytest.mark.parametrize(
    ("setup", "iterable"),
    [
        ("", '("A", "B")'),
        ("", '["B", "A"]'),
        ('A_LABEL = "A"\nB_LABEL = "B"', "(B_LABEL, A_LABEL)"),
        ('GROUPS = ("A", "B")', "GROUPS"),
    ],
)
def test_v22_exact_contract_domain_iterables_reconstruct_two_members(
    setup: str,
    iterable: str,
) -> None:
    result = _analyze(_v22_reconstruction_source(setup=setup, iterable=iterable))
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.group_values == _GROUPS


@pytest.mark.parametrize(
    ("iterable", "body_before_store", "loop_else"),
    [
        ('("A",)', "", ""),
        ('("A", "B", "C")', "", ""),
        ('("A", "A")', "", ""),
        ('("A", "outside")', "", ""),
        ('("A", str("B"))', "", ""),
        ('("A", "B")', '    level = "A"\n', ""),
        ('("A", "B")', "", 'else:\n    print("done")\n'),
    ],
)
def test_v22_nonclosed_contract_domain_loop_never_completes_operands(
    iterable: str,
    body_before_store: str,
    loop_else: str,
) -> None:
    assert (
        _analyze(
            _v22_reconstruction_source(
                iterable=iterable,
                body_before_store=body_before_store,
                loop_else=loop_else,
            )
        ).reason
        == "two-group-row-selection-unavailable"
    )


@pytest.mark.parametrize(
    ("after_loop", "left", "right", "expected_reason"),
    [
        ("", 'summary.get("A")', 'summary.get("B")', "unregistered-component-consumer"),
        ('summary["C"] = df["value"]', 'summary["A"]', 'summary["B"]', "tracked-value-mutation"),
        ('del summary["A"]', 'summary["A"]', 'summary["B"]', "tracked-value-mutation"),
        (
            'summary.update({"A": df["value"]})',
            'summary["A"]',
            'summary["B"]',
            "unregistered-component-consumer",
        ),
        ("alias = summary", 'alias["A"]', 'alias["B"]', "two-group-row-selection-unavailable"),
    ],
)
def test_v22_reconstruction_refuses_nonmember_preserving_uses(
    after_loop: str,
    left: str,
    right: str,
    expected_reason: str,
) -> None:
    assert (
        _analyze(_v22_reconstruction_source(after_loop=after_loop, left=left, right=right)).reason
        == expected_reason
    )


def test_v22_whole_reconstruction_escape_suppresses_unrelated_raw_test() -> None:
    source = _source(
        before_test=(
            "summary = {}\n"
            'for level in ("A", "B"):\n'
            '    values = df.loc[df["group"] == level, "value"]\n'
            "    summary[level] = values\n"
            "alias = summary"
        ),
    )
    assert _analyze(source).reason == "unregistered-component-consumer"


@pytest.mark.parametrize(
    "loop_body",
    [
        "        values = helper.select_group(df, level)\n        print(values)",
        "        values = print(select_group(df, level))",
    ],
)
def test_v22_non_simple_or_nested_loop_helper_call_never_expands(loop_body: str) -> None:
    source = f"""import pandas as pd
from scipy import stats

def select_group(frame, level):
    return frame.loc[frame["group"] == level, "value"]

def main():
    df = pd.read_csv("data.csv")
    left = df.loc[df["group"] == "A", "value"]
    right = df.loc[df["group"] == "B", "value"]
    for level in ("A", "B"):
{loop_body}
    result = stats.ttest_ind(left, right)
    print(result.pvalue)

if __name__ == "__main__":
    main()
""".encode()
    assert _analyze(source).reason is not None


def test_v22_loop_and_reconstruction_are_prose_byte_invariant() -> None:
    template = '''"""{doc}"""
# {comment}
import pandas as pd
from scipy import stats
GROUPS = ("A", "B")
def main():
    df = pd.read_csv("data.csv")
    summary = {{}}
    for level in GROUPS:
        values = df.loc[df["group"] == level, "value"]
        summary[level] = values
        print("{label}", level, values.mean())
    left = summary["A"]
    right = summary["B"]
    result = stats.ttest_ind(left, right)
    print("{result_label}", result.pvalue)
if __name__ == "__main__":
    main()
'''
    variants = [
        ("AAAAAAAA", "BBBBBBBB", "CCCCCCCC", "DDDDDDDD"),
        ("averaged", "independ", "explore!", "primary!"),
        ("mixedmod", "no-avera", "pseudobl", "row-wise"),
    ]
    results = [
        _analyze(
            template.format(
                doc=doc,
                comment=comment,
                label=label,
                result_label=result_label,
            ).encode()
        )
        for doc, comment, label, result_label in variants
    ]
    assert all(result.reason is None and result.facts is not None for result in results)
    assert results[0].facts == results[1].facts == results[2].facts
