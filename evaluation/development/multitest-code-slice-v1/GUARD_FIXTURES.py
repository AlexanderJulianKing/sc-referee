"""Answer-visible source fixtures for the development-only multiple-testing code slice."""

from __future__ import annotations


def explicit(
    *,
    columns: tuple[str, ...] = ("m1", "m2", "m3"),
    imports: str = "",
    before: str = "",
    decisions: str | None = None,
    after: str = "",
) -> str:
    calls = "\n".join(
        f'r{index} = stats.ttest_ind(df.loc[df["group"] == "a", "{column}"], '
        f'df.loc[df["group"] == "b", "{column}"])'
        for index, column in enumerate(columns)
    )
    if decisions is None:
        decisions = "\n".join(f"print(r{index}.pvalue < 0.05)" for index in range(len(columns)))
    return (
        "import pandas as pd\nfrom scipy import stats\n"
        + imports
        + 'df = pd.read_csv("data.csv")\n'
        + before
        + calls
        + "\n"
        + decisions
        + "\n"
        + after
    )


FIVE = ("m1", "m2", "m3", "m4", "m5")

FIXTURES = {
    "correct-default-method-multipletests": {
        "columns": ("m1", "m2", "m3"),
        "expected": "covered-negative",
        "source": explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=(
                "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
                "reject, adjusted, _, _ = multipletests(pvalues)\n"
                "print(reject[0])\nprint(reject[1])\nprint(reject[2])"
            ),
        ),
    },
    "correct-hand-sidak": {
        "columns": ("m1", "m2", "m3"),
        "expected": "unresolved-decision-threshold",
        "source": explicit(
            decisions=(
                "threshold = 1 - (1 - 0.05) ** (1 / 3)\n"
                "print(r0.pvalue < threshold)\nprint(r1.pvalue < threshold)\n"
                "print(r2.pvalue < threshold)"
            )
        ),
    },
    "correct-bare-literal-bonferroni-off-ast": {
        "columns": FIVE,
        "expected": "unresolved-decision-threshold",
        "source": explicit(
            columns=FIVE,
            decisions="\n".join(f"print(r{i}.pvalue < 0.01)" for i in range(5)),
        ),
    },
    "correct-off-registry-correction": {
        "columns": ("m1", "m2", "m3"),
        "expected": "unresolved-manual-correction-present",
        "source": explicit(
            imports="import pingouin\n",
            after="pingouin.multicomp([r0.pvalue, r1.pvalue, r2.pvalue])\n",
        ),
    },
    "correct-sensitivity-duplicate": {
        "columns": ("m1", "m2", "m3"),
        "expected": "extra-registered-test-outside-authorized-family",
        "source": explicit(
            before=(
                'sensitivity = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], '
                'df.loc[df["group"] == "b", "m1"])\n'
            )
        ),
    },
    "correct-discovery-validation-split": {
        "columns": ("m1", "m2", "m3"),
        "expected": "selected-group-row-completeness-unproven",
        "source": (
            "import pandas as pd\nfrom scipy import stats\n"
            'df = pd.read_csv("data.csv")\n'
            + "\n".join(
                f'r{i} = stats.ttest_ind(df.loc[(df["group"] == "a") & '
                f'(df["{column}"] > 0), "{column}"], df.loc[(df["group"] == "b") & '
                f'(df["{column}"] > 0), "{column}"])'
                for i, column in enumerate(("m1", "m2", "m3"))
            )
            + "\nprint(r0.pvalue < 0.05)\nprint(r1.pvalue < 0.05)\n"
            + "print(r2.pvalue < 0.05)\n"
        ),
    },
    "correct-upstream-adjusted-input": {
        "columns": ("m1", "m2", "m3"),
        "expected": "upstream-correction-lineage-unresolved",
        "source": explicit(
            imports="import numpy\n",
            after=(
                'adjusted = numpy.load("adjusted.npy")\n'
                "print(adjusted[0] < 0.05)\nprint(adjusted[1] < 0.05)\n"
                "print(adjusted[2] < 0.05)\n"
            ),
        ),
    },
    "correct-cross-module-numpy-correction-helper": {
        "columns": ("m1", "m2", "m3"),
        "expected": "unresolved-pvalue-consumer",
        "source": explicit(
            imports="from external_adjustment import adjust_values\n",
            after="adjust_values([r0.pvalue, r1.pvalue, r2.pvalue])\n",
        ),
    },
    "correct-export-for-downstream-correction": {
        "columns": ("m1", "m2", "m3"),
        "expected": "unresolved-pvalue-consumer",
        "source": explicit(
            after=(
                "pvalues = pd.Series([r0.pvalue, r1.pvalue, r2.pvalue])\n"
                'pvalues.to_csv("pvalues.csv")\n'
            )
        ),
    },
    "correct-all-numpy-omnibus-gate": {
        "columns": ("m1", "m2", "m3"),
        "expected": "hierarchical-gatekeeping-present",
        "source": explicit(
            imports="import numpy\n",
            before=(
                'gate = numpy.abs(numpy.mean(df[["m1", "m2", "m3"]].to_numpy(), '
                "axis=0)).sum()\nif gate > 0:\n    ready = True\n"
            ),
        ),
    },
    "correct-numpy-omnibus-assert-gate": {
        "columns": ("m1", "m2", "m3"),
        "expected": "hierarchical-gatekeeping-present",
        "source": explicit(
            imports="import numpy\n",
            before=(
                'gate = numpy.abs(numpy.mean(df[["m1", "m2", "m3"]].to_numpy(), '
                "axis=0)).sum()\nassert gate > 0\n"
            ),
        ),
    },
    "correct-disjoint-correction-families": {
        "columns": ("m1", "m2", "m3"),
        "expected": "multiple-family-partition-present",
        "source": explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=(
                "first = [r0.pvalue]\nsecond = [r1.pvalue, r2.pvalue]\n"
                "reject_first, _, _, _ = multipletests(first)\n"
                "reject_second, _, _, _ = multipletests(second)\n"
                "print(reject_first[0])\nprint(reject_second[0])\n"
                "print(reject_second[1])"
            ),
        ),
    },
    "correct-label-permutation-maxT": {
        "columns": ("m1", "m2", "m3"),
        "expected": "permutation-family-control-present",
        "source": explicit(
            after=(
                "null = []\nfor _ in range(20):\n    permuted = df.sample(frac=1)\n"
                '    null.append(max(permuted["m1"]))\n'
            )
        ),
    },
    "correct-unresolved-cardinality-maxT": {
        "columns": ("m1", "m2", "m3"),
        "expected": "resampling-cardinality-unresolved",
        "source": explicit(
            after=(
                "null = []\nfor _ in range(20 * len(df)):\n"
                "    permuted = df.sample(frac=1)\n"
                '    null.append(max(permuted["m1"]))\n'
            )
        ),
    },
    "correct-off-family-survival-sibling": {
        "columns": ("m1", "m2", "m3"),
        "expected": "unresolved-inference-sibling-present",
        "source": explicit(
            imports="import lifelines\n",
            after='lifelines.CoxPHFitter().fit(df, duration_col="m1")\n',
        ),
    },
    "correct-minimum-p-global-summary": {
        "columns": ("m1", "m2", "m3"),
        "expected": "family-pvalue-extremum-reduction-present",
        "source": explicit(after="print(min([r0.pvalue, r1.pvalue, r2.pvalue]))\n"),
    },
    "correct-pvalue-table-only": {
        "columns": ("m1", "m2", "m3"),
        "expected": "pderived-conclusion-family-incomplete",
        "source": explicit(decisions="print(r0.pvalue)\nprint(r1.pvalue)\nprint(r2.pvalue)"),
    },
}
