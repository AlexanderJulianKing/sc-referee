from __future__ import annotations

import ast

import pytest

import sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1 as dataflow
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import _parse_csv

CSV = (
    b"unit,group,value,visit\n"
    b"u1,a,1,1\n"
    b"u1,a,2,2\n"
    b"u2,a,3,1\n"
    b"u2,a,4,2\n"
    b"u3,b,5,1\n"
    b"u3,b,6,2\n"
    b"u4,b,7,1\n"
    b"u4,b,8,2\n"
)


def _run(source: str) -> dataflow.CodeDataflowResult:
    return dataflow.analyze_code_csv_dataflow(
        source.encode(),
        authorized_path="data.csv",
        unit_column="unit",
        group_column="group",
        csv_header=("unit", "group", "value", "visit"),
        group_values=("a", "b"),
        csv_content=CSV,
    )


def _candidate(extra: str = "", *, left: str | None = None, right: str | None = None) -> str:
    left = left or 'df.loc[df["group"] == "a", "value"]'
    right = right or 'df.loc[df["group"] == "b", "value"]'
    return f"""import pandas as pd
from scipy import stats
df = pd.read_csv("data.csv")
a = {left}
b = {right}
{extra}
t, p = stats.ttest_ind(a, b)
print(p)
"""


def test_h1_local_d1_rule_drops_only_the_distinct_le_m_seam() -> None:
    csv_bytes = (
        b"unit,group,index,value\n"
        b"u1,a,a,1\n"
        b"u1,a,b,2\n"
        b"u1,a,c,3\n"
        b"u2,a,b,4\n"
        b"u2,a,c,5\n"
        b"u2,a,d,6\n"
        b"u3,b,a,7\n"
        b"u3,b,c,8\n"
        b"u3,b,d,9\n"
        b"u4,b,a,10\n"
        b"u4,b,b,11\n"
        b"u4,b,d,12\n"
    )
    facts = _parse_csv(csv_bytes, "unit", "group")
    assert not isinstance(facts, str)
    assert facts.maximum_multiplicity == 3
    assert "index" in facts.within_unit_index_columns
    assert facts.unique_nonindex_columns == ()


def test_h1_still_abstains_when_not_every_declared_unit_repeats() -> None:
    csv_bytes = (
        b"unit,group,site,value\n"
        b"u1,a,north,1\n"
        b"u1,a,south,2\n"
        b"u2,a,north,3\n"
        b"u3,b,south,4\n"
        b"u3,b,east,5\n"
    )
    facts = _parse_csv(csv_bytes, "unit", "group")
    assert not isinstance(facts, str)
    assert facts.unique_nonindex_columns == ("site",)


def test_h2_closed_lambda_inside_inlined_helper_is_admitted() -> None:
    source = """import pandas as pd
from scipy import stats
def describe(df):
    return df.groupby("group")["value"].agg(sd=lambda s: s.std(ddof=1))
def compare(df):
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    return stats.ttest_ind(a, b)
def main():
    df = pd.read_csv("data.csv")
    summary = describe(df)
    result = compare(df)
    print(result.pvalue)
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason is None


def test_h2_lambda_capture_of_tracked_frame_abstains() -> None:
    source = """import pandas as pd
from scipy import stats
def compare(df):
    formatter = lambda value: value + len(df)
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    result = stats.ttest_ind(a, b)
    return formatter(result.pvalue)
def main():
    df = pd.read_csv("data.csv")
    p = compare(df)
    print(p)
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason == "helper-closure-or-nested-definition-unsupported"


def test_h3_if_return_output_helper_preserves_p_sink() -> None:
    source = """import pandas as pd
from scipy import stats
def format_p(value):
    if value < 0.001:
        return value * 1000
    return value
def main():
    df = pd.read_csv("data.csv")
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    t, p = stats.ttest_ind(a, b)
    print(format_p(p))
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason is None


def test_h3_if_return_helper_reading_tracked_frame_is_not_pure() -> None:
    source = """import pandas as pd
from scipy import stats
def format_p(value, df):
    if len(df) > 1:
        return value
    return value
def main():
    df = pd.read_csv("data.csv")
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    t, p = stats.ttest_ind(a, b)
    print(format_p(p, df))
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason == "test-result-output-sink-unavailable"


def test_h4_count_only_unit_summary_does_not_fire_s5() -> None:
    extra = 'print(df.groupby("unit").size().unique().tolist())'
    assert _run(_candidate(extra)).reason is None


def test_h4_count_and_value_mean_coexistence_still_fires_s5() -> None:
    extra = """print(df.groupby("unit").size().unique().tolist())
print(df.groupby("unit")["value"].mean())"""
    assert _run(_candidate(extra)).reason == "unit-level-summary-sibling-present"


def test_h5_inlined_helper_tuple_return_advances_but_does_not_create_a_new_p_sink() -> None:
    source = """import pandas as pd
from scipy import stats
def compare(df):
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    t, p = stats.ttest_ind(a, b)
    return t, p, a, b
def main():
    df = pd.read_csv("data.csv")
    t, p, a, b = compare(df)
    print(p)
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason == "test-result-output-sink-unavailable"


def test_h5_nonliteral_helper_destructuring_does_not_create_operand_edges() -> None:
    source = """import pandas as pd
from scipy import stats
def compare(df):
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    return list(stats.ttest_ind(a, b))
def main():
    df = pd.read_csv("data.csv")
    t, p = compare(df)
    print(p)
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason is not None


@pytest.mark.parametrize(
    "iterable",
    [
        'df["group"].unique()',
        'sorted(df["group"].unique())',
        'set(df["group"])',
    ],
)
def test_h6_observed_contract_domain_loop_unrolls(iterable: str) -> None:
    source = f"""import pandas as pd
from scipy import stats
df = pd.read_csv("data.csv")
groups = {{}}
for level in {iterable}:
    groups[level] = df.loc[df["group"] == level, "value"]
a = groups["a"]
b = groups["b"]
t, p = stats.ttest_ind(a, b)
print(p)
"""
    assert _run(source).reason is None


def test_h6_observed_domain_mismatch_abstains() -> None:
    source = """import pandas as pd
from scipy import stats
df = pd.read_csv("data.csv")
groups = {}
for level in sorted(df["visit"].unique()):
    groups[level] = df.loc[df["group"] == level, "value"]
a = groups["a"]
b = groups["b"]
t, p = stats.ttest_ind(a, b)
print(p)
"""
    assert _run(source).reason is not None


def test_h7_append_join_buffer_returned_by_print_helper_is_p_sink() -> None:
    source = """import pandas as pd
from scipy import stats
def compare(df):
    a = df.loc[df["group"] == "a", "value"]
    b = df.loc[df["group"] == "b", "value"]
    t, p = stats.ttest_ind(a, b)
    return {"t": t, "p": p}
def report(result):
    lines = []
    lines.append("result")
    lines.append("p = %g" % result["p"])
    return "\\n".join(lines)
def main():
    df = pd.read_csv("data.csv")
    result = compare(df)
    print(report(result))
if __name__ == "__main__":
    main()
"""
    assert _run(source).reason is None


def test_h7_buffer_without_p_payload_does_not_establish_sink() -> None:
    source = _candidate().replace(
        "print(p)",
        """lines = []
lines.append("constant")
print("\\n".join(lines))""",
    )
    assert _run(source).reason == "test-result-output-sink-unavailable"


def test_direct_candidate_requires_repeated_rows_in_each_selected_group() -> None:
    result = _run(_candidate())
    assert result.reason is None
    assert result.facts is not None
    assert result.facts.value_column == "value"


@pytest.mark.parametrize(
    "sibling",
    [
        'import statsmodels.formula.api as smf\nmodel = smf.mixedlm("value ~ group", df, groups=df["unit"])\nfit = model.fit()',
        'class Model:\n    def fit(self):\n        return 1\nmodel = Model(group_data=df["unit"])\nfit = model.fit()',
        'class Model:\n    def fit(self):\n        return 1\nmodel = Model(groups=df["unit"])\nfit = model.fit()',
        'class Model:\n    def fit(self):\n        return 1\nmodel = Model(re_formula="~1")\nfit = model.fit()',
        'class Model:\n    def fit(self):\n        return 1\nmodel = Model(cluster=df["unit"])\nfit = model.fit()',
        'import statsmodels.api as sm\nmodel = sm.OLS(a, b)\nfit = model.fit(cov_type="cluster")',
    ],
)
def test_s1_dependence_guard_is_full_scope_and_keyword_closed(sibling: str) -> None:
    assert _run(_candidate(sibling)).reason == "dependence-aware-sibling-present"


@pytest.mark.parametrize("prefix", ["gpboost", "merf", "pymc", "numpyro", "linearmodels"])
def test_s3_closed_statistics_prefixes_abstain(prefix: str) -> None:
    source = _candidate(f"import {prefix}\nother = {prefix}.unknown_model(a)")
    assert _run(source).reason == "unresolved-inference-sibling-present"


def test_s4_counts_a_dead_branch_registered_test_before_operand_resolution() -> None:
    extra = """if False:
    stats.ttest_ind(df.head(1), df.tail(1))"""
    assert _run(_candidate(extra)).reason == "multiple-rowwise-test-candidates"


@pytest.mark.parametrize(
    "size",
    ["(N_BOOT, len(a))", "(len(a), N_BOOT)"],
)
def test_s2_vectorized_draw_uses_any_resolved_large_size_factor(size: str) -> None:
    extra = f"""import numpy as np
N_BOOT = 20_000
rng = np.random.default_rng(7)
draws = rng.integers(0, len(a), size={size})
boot = a.to_numpy()[draws].mean(axis=1)
lo = np.percentile(boot, 2.5)
print(lo)"""
    result = _run(_candidate(extra))
    assert result.reason == "resampling-inference-sibling-present"


def test_s2_count_ratio_and_threshold_ten() -> None:
    extra = """import numpy as np
reps = []
for i in range(49):
    reps.append(a.iloc[i % len(a)])
r = np.sum(np.asarray(reps) >= a.mean())
p_boot = (r + 1) / (49 + 1)
print(p_boot)"""
    assert _run(_candidate(extra)).reason == "resampling-inference-sibling-present"


def test_s2_called_helper_is_censused_over_the_full_module() -> None:
    source = _candidate(
        """def bootstrap_ci(values, n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    ci = sum(draws) / len(draws)
    print(ci)
bootstrap_ci(a)"""
    )
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_uncalled_helper_is_censused_over_the_full_module() -> None:
    source = _candidate(
        """def bootstrap_ci(n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(a.iloc[index % len(a)])
    ci = sum(draws) / len(draws)
    print(ci)"""
    )
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_class_method_is_censused_over_the_full_module() -> None:
    source = _candidate(
        """class Bootstrap:
    def run(self, values, n_resamples=2_000):
        draws = []
        for index in range(n_resamples):
            draws.append(values.iloc[index % len(values)])
        ci = sum(draws) / len(draws)
        print(ci)
Bootstrap().run(a)"""
    )
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_reduction_returned_by_helper_reaches_caller_print() -> None:
    source = _candidate(
        """def bootstrap_ci(values, n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    return np.percentile(draws, 2.5)
lo = bootstrap_ci(a)
print(lo)"""
    ).replace("import pandas as pd", "import pandas as pd\nimport numpy as np")
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_frame_parameter_dict_member_return_reaches_caller_print() -> None:
    source = _candidate(
        """def bootstrap_ci(frame, n_resamples=2_000):
    draws = []
    values = frame.loc[frame["group"] == "a", "value"]
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    return {"lo": np.percentile(draws, 2.5), "label": "bootstrap"}
ci = bootstrap_ci(df)
print(ci["lo"])"""
    ).replace("import pandas as pd", "import pandas as pd\nimport numpy as np")
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_two_deep_helper_return_tuple_member_reaches_caller_print() -> None:
    source = _candidate(
        """def inner_ci(values, n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    return (np.percentile(draws, 2.5), np.percentile(draws, 97.5))
def outer_ci(values):
    return inner_ci(values)
lo, hi = outer_ci(a)
print(lo)"""
    ).replace("import pandas as pd", "import pandas as pd\nimport numpy as np")
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s2_unprinted_return_member_does_not_reach_caller_sink() -> None:
    source = _candidate(
        """def bootstrap_ci(values, n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    return {"lo": np.percentile(draws, 2.5), "label": "bootstrap"}
ci = bootstrap_ci(a)
print(ci["label"])"""
    ).replace("import pandas as pd", "import pandas as pd\nimport numpy as np")
    assert _run(source).facts is not None


def test_s2_precedes_s3_independently_of_source_position() -> None:
    source = _candidate(
        """other = stats.pearsonr(a, b)
def bootstrap_ci(values, n_resamples=2_000):
    draws = []
    for index in range(n_resamples):
        draws.append(values.iloc[index % len(values)])
    ci = sum(draws) / len(draws)
    print(ci)
bootstrap_ci(a)"""
    )
    assert _run(source).reason == "resampling-inference-sibling-present"


def test_s5_hand_written_unit_welch_with_math_erf_suppresses() -> None:
    extra = """import math
unit_means = df.groupby("unit")["value"].mean()
welch = unit_means.mean() / unit_means.std()
p_unit = math.erf(abs(welch))
print(p_unit)"""
    assert _run(_candidate(extra)).reason == "unit-level-summary-sibling-present"


def test_s5_unit_summary_helper_return_reaches_caller_print() -> None:
    extra = """def per_unit_summary(frame):
    means = frame.groupby("unit")["value"].mean()
    return {"means": means.to_dict(), "label": "per unit"}
summary = per_unit_summary(df)
print(summary["means"])"""
    assert _run(_candidate(extra)).reason == "unit-level-summary-sibling-present"


def test_s5_unit_consistency_check_that_only_raises_is_not_output() -> None:
    extra = """counts = df.groupby("unit")["value"].size()
if counts.min() < 2:
    raise ValueError("bad")"""
    assert _run(_candidate(extra)).facts is not None


def test_statistic_only_sink_does_not_satisfy_p_result_output() -> None:
    source = _candidate().replace("print(p)", "print(t)")
    assert _run(source).reason == "test-result-output-sink-unavailable"


def test_only_test_in_dead_branch_is_not_a_candidate() -> None:
    source = _candidate().replace(
        "t, p = stats.ttest_ind(a, b)\nprint(p)",
        "if False:\n    t, p = stats.ttest_ind(a, b)\n    print(p)",
    )
    assert _run(source).reason == "test-result-output-sink-unavailable"


@pytest.mark.parametrize(
    ("transform", "expected"),
    [
        (
            'df.loc[df["group"] == "a", "value"].iloc[:2]',
            "selected-group-row-completeness-unproven",
        ),
        ('df.loc[df["group"] == "a", "value"].head(2)', "aggregation-on-test-operand-path"),
        ('df.loc[df["group"] == "a", "value"].sample(2)', "aggregation-on-test-operand-path"),
        (
            'df.loc[(df["group"] == "a") & (df.groupby("unit").cumcount() == 0), "value"]',
            "aggregation-on-test-operand-path",
        ),
        ('df.loc[df["group"] == "a", "value"].rank()', "aggregation-on-test-operand-path"),
        ('df.loc[df["group"] == "a", "value"].diff()', "aggregation-on-test-operand-path"),
        (
            'df.loc[df["group"] == "a", "value"].rolling(2).mean()',
            "aggregation-on-test-operand-path",
        ),
        (
            'df.loc[df["group"] == "a", "value"].ewm(span=2).mean()',
            "aggregation-on-test-operand-path",
        ),
        (
            'df.loc[df["group"] == "a", "value"].transform("mean")',
            "aggregation-on-test-operand-path",
        ),
    ],
)
def test_row_collapse_and_reducing_transforms_abstain(transform: str, expected: str) -> None:
    result = _run(_candidate(left=transform))
    assert result.reason == expected


def test_numpy_log_is_a_nonreducing_operand_edge() -> None:
    source = _candidate(
        "import numpy as np",
        left='np.log(df.loc[df["group"] == "a", "value"])',
        right='np.log(df.loc[df["group"] == "b", "value"])',
    )
    assert _run(source).facts is not None


def test_drop_duplicates_on_unit_column_is_reducing_on_operand_path() -> None:
    source = """import pandas as pd
from scipy import stats
df = pd.read_csv("data.csv")
reduced = df.drop_duplicates(subset="unit")
a = reduced.loc[reduced["group"] == "a", "value"]
b = reduced.loc[reduced["group"] == "b", "value"]
t, p = stats.ttest_ind(a, b)
print(p)
"""
    assert _run(source).reason == "aggregation-on-test-operand-path"


def test_iloc_last_row_per_unit_before_group_selection_cannot_restore_completeness() -> None:
    source = """import pandas as pd
from scipy import stats
full = pd.read_csv("data.csv")
data = full.iloc[[1, 3, 5, 7]]
a = data.loc[data["group"] == "a", "value"]
b = data.loc[data["group"] == "b", "value"]
t, p = stats.ttest_ind(a, b)
print(p)
"""
    assert _run(source).reason == "selected-group-row-completeness-unproven"


def test_dropna_before_group_selection_cannot_restore_completeness() -> None:
    source = """import pandas as pd
from scipy import stats
full = pd.read_csv("data.csv")
data = full.dropna(subset=["value"])
a = data.loc[data["group"] == "a", "value"]
b = data.loc[data["group"] == "b", "value"]
t, p = stats.ttest_ind(a, b)
print(p)
"""
    assert _run(source).reason == "selected-group-row-completeness-unproven"


def test_dropna_after_group_selection_requires_csv_nonmissing_proof() -> None:
    source = _candidate(
        left='df.loc[df["group"] == "a", "value"].dropna()',
    )
    assert _run(source).reason == "selected-group-row-completeness-unproven"


def test_arbitrary_off_path_calls_do_not_gate_operand_identity() -> None:
    extra = """def describe(x):
    return {"text": sorted(str(v) for v in x)}
print(describe(a))"""
    assert _run(_candidate(extra)).facts is not None


def test_new_guard_and_slice_entry_points_never_receive_prose_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: set[str] = set()
    targets = (
        ("_v3_dependence_guard", dataflow, "_v3_dependence_guard"),
        ("_v2_resampling_sibling", dataflow, "_v2_resampling_sibling"),
        ("_v3_statistics_guard", dataflow, "_v3_statistics_guard"),
        ("_v3_syntactic_test_count", dataflow, "_v3_syntactic_test_count"),
        ("_v3_unit_summary_guard", dataflow, "_v3_unit_summary_guard"),
        ("_csv_group_unit_lineage", dataflow, "_csv_group_unit_lineage"),
        ("_operand_rows_complete", dataflow._Analyzer, "_operand_rows_complete"),
        ("_v3_call_reachable", dataflow, "_v3_call_reachable"),
        ("_result_sinks", dataflow._Analyzer, "_result_sinks"),
        ("_aggregation_call", dataflow, "_aggregation_call"),
    )
    for label, owner, name in targets:
        original = getattr(owner, name)

        def guarded(
            *args: object, __name: str = label, __original: object = original, **kwargs: object
        ) -> object:
            assert all(
                not isinstance(value, str) or "report prose sentinel" not in value for value in args
            )
            assert all(
                not isinstance(value, (bytes, bytearray)) or b"report prose sentinel" not in value
                for value in args
            )
            called.add(__name)
            return __original(*args, **kwargs)  # type: ignore[operator]

        monkeypatch.setattr(owner, name, guarded)

    source = _candidate(
        'ranked = a.rank()\nlabel = "report prose sentinel"\nprint(ranked)\nprint(label)'
    )
    assert _run(source).facts is not None
    assert called == {label for label, _, _ in targets}


def test_docstrings_comments_and_unrelated_strings_do_not_change_facts() -> None:
    baseline = _run(
        '"""alpha prose sentinel"""\n# alpha prose sentinel\n'
        + _candidate('label = "alpha"\nprint(label)')
    )
    mutated = _run(
        '"""omega prose sentinel"""\n# omega prose sentinel\n'
        + _candidate('label = "omega"\nprint(label)')
    )
    assert baseline == mutated


def test_module_ast_is_parsed_without_executing_source(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    original = ast.parse

    def counted(*args: object, **kwargs: object) -> ast.Module:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(ast, "parse", counted)
    assert _run(_candidate()).facts is not None
    assert calls == 1
