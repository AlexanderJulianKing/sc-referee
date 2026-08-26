"""Answer-visible MT 2.1 false-accusation and surviving-guard fixtures."""

from __future__ import annotations

from pathlib import Path


def _explicit(
    *,
    imports: str = "",
    before: str = "",
    decisions: str | None = None,
    after: str = "",
    columns: tuple[str, ...] = ("m1", "m2", "m3"),
) -> str:
    calls = "\n".join(
        f'r{index} = stats.ttest_ind(df.loc[df["group"] == "a", "{column}"], '
        f'df.loc[df["group"] == "b", "{column}"])'
        for index, column in enumerate(columns)
    )
    conclusions = decisions or "\n".join(
        f"print(r{index}.pvalue < 0.05)" for index in range(len(columns))
    )
    return (
        "import pandas as pd\nfrom scipy import stats\n"
        + imports
        + 'df = pd.read_csv("data.csv")\n'
        + before
        + calls
        + "\n"
        + conclusions
        + "\n"
        + after
    )


def _masked_operands(*, dtype: str = "") -> str:
    source = _explicit()
    for column in ("m1", "m2", "m3"):
        for group in ("a", "b"):
            source = source.replace(
                f'df.loc[df["group"] == "{group}", "{column}"]',
                f'df.loc[(df["group"] == "{group}") & (df["m1"] > 0), "{column}"]' + dtype,
            )
    return source


_COMPLETE = (
    "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
    "reject, adjusted, _, _ = multipletests(pvalues)\n"
    "print(reject[0]); print(reject[1]); print(reject[2])"
)

_EARLY_RETURN = """import numpy as np
import pandas as pd
from scipy import stats
OUTCOMES = ["m1", "m2", "m3"]
def main():
    df = pd.read_csv("data.csv")
    panel = np.abs(np.mean(df[OUTCOMES].to_numpy(), axis=0)).sum()
    if panel < 1:
        return
    r0 = stats.ttest_ind(df.loc[df["group"] == "a", "m1"], df.loc[df["group"] == "b", "m1"])
    r1 = stats.ttest_ind(df.loc[df["group"] == "a", "m2"], df.loc[df["group"] == "b", "m2"])
    r2 = stats.ttest_ind(df.loc[df["group"] == "a", "m3"], df.loc[df["group"] == "b", "m3"])
    print(r0.pvalue < 0.05); print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)
if __name__ == "__main__":
    main()
"""

_R12_SEQUENCE = (
    "p = r0.pvalue\nprint(p < 0.05)\n"
    "p = r1.pvalue\nprint(p < 0.05)\n"
    "p = r2.pvalue\nprint(p < 0.05)\n"
)

_R15_UNRESOLVED_STORE = """import pandas as pd
from scipy import stats
OUTCOMES = ["m1", "m2", "m3"]
df = pd.read_csv("data.csv")
results = {}
for column in OUTCOMES:
    a = df.loc[df["group"] == "a", column]
    b = df.loc[df["group"] == "b", column]
    r = stats.ttest_ind(a, b)
    results[column] = {"p_value": r.pvalue, "mean": a.mean()}
field = "mean"
results[OUTCOMES[0]][field] = results[OUTCOMES[0]]["p_value"]
for column in OUTCOMES:
    result = results[column]
    difference = result["mean"] - 0
    print(column, difference, result["p_value"] < 0.05)
"""

_SPEC49_R6 = (
    Path("evaluation/development/multitest-open-corpus-v1/cases/spec-49/analysis.py")
    .read_text(encoding="utf-8")
    .replace("cutoff = 0.05", "cutoff = 0.05 / 6")
)

_R16_COMPLETE = """import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
OUTCOMES = ["m1", "m2", "m3"]
df = pd.read_csv("data.csv")
pvalues = []
for column in OUTCOMES:
    a = df.loc[df["group"] == "a", column]
    b = df.loc[df["group"] == "b", column]
    pvalues.append(stats.ttest_ind(a, b).pvalue)
reject, adjusted, _, _ = multipletests(pvalues)
for column, p, q, flag in zip(OUTCOMES, pvalues, adjusted, reject):
    print(column, p, q, flag)
"""

FIXTURES = {
    "correct-offslice-hand-holm-definition": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            after="def hand_holm(values):\n    return values\nhand_holm([r0.pvalue, r1.pvalue, r2.pvalue])\n"
        ),
    },
    "correct-offslice-try-with-finally-correction": {
        "expected": "unresolved-manual-correction-present",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            after="def unused():\n    try:\n        return 1\n    finally:\n        multipletests([0.01, 0.02, 0.03])\n",
        ),
    },
    "correct-offslice-custom-adjuster-import": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            imports="from custom_adjustment import westfall_adjust\n",
            after="westfall_adjust([r0.pvalue, r1.pvalue, r2.pvalue])\n",
        ),
    },
    "correct-offslice-helper-plus-complete-correction": {
        "expected": "covered-negative",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions="def unrelated(value):\n    return value + 1\n" + _COMPLETE,
        ),
    },
    "correct-unused-sensitivity-helper": {
        "expected": "extra-registered-test-outside-authorized-family",
        "source": _explicit(
            after='def unused():\n    return stats.ttest_ind(df.loc[df["group"] == "a", "m1"], df.loc[df["group"] == "b", "m1"])\n'
        ),
    },
    "correct-unused-holm-call": {
        "expected": "unresolved-manual-correction-present",
        "source": _explicit(after="def unused():\n    return holm([0.1, 0.2, 0.3])\n"),
    },
    "correct-unused-shapiro-helper": {
        "expected": "unresolved-inference-sibling-present",
        "source": _explicit(after="def unused():\n    return stats.shapiro([1, 2, 3])\n"),
    },
    "correct-eval-based-correction-helper": {
        "expected": "api-resolution-ambiguous",
        "source": _explicit(after='def unused():\n    return eval("adjusted")\n'),
    },
    "correct-monkeypatched-statistics-correction": {
        "expected": "api-resolution-ambiguous",
        "source": _explicit(after="stats.ttest_ind = replacement\n"),
    },
    "correct-nonalias-terminal-name-with-complete-correction": {
        "expected": "covered-negative",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions="ttest_ind = 7\nbenjamini_hochberg = 8\n" + _COMPLETE,
        ),
    },
    "correct-unused-secondary-reader": {
        "expected": "candidate",
        "source": _explicit(after='def unused():\n    return pd.read_csv("other.csv")\n'),
    },
    "correct-mixed-reader-family-operand": {
        "expected": "additional-accepted-reader-present",
        "source": _explicit(after='other = pd.read_csv("other.csv")\n').replace(
            'df.loc[df["group"] == "a", "m1"]',
            'other.loc[other["group"] == "a", "m1"]',
            1,
        ),
    },
    "correct-outcome-alias-pop-in-unused-helper": {
        "expected": "analysis-scope-structure-unsupported",
        "source": _explicit(
            after='OUTCOMES = ["m1", "m2", "m3"]\ndef unused():\n    OUTCOMES.pop()\n'
        ),
    },
    "correct-helper-row-filter": {
        "expected": "selected-group-row-completeness-unproven",
        "source": _explicit().replace(
            'df.loc[df["group"] == "a", "m1"]',
            'df.loc[(df["group"] == "a") & (df["m2"] > 0), "m1"]',
            1,
        ),
    },
    "correct-position-one-then-holm": {
        "expected": "covered-negative",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=(
                "pvalues = [r0[1], r1[1], r2[1]]\n"
                'reject, adjusted, _, _ = multipletests(pvalues, method="holm")\n'
                "print(reject[0]); print(reject[1]); print(reject[2])"
            ),
        ),
    },
    "correct-float-p-hand-bonferroni": {
        "expected": "covered-negative",
        "source": _explicit(
            decisions=(
                "a0 = min(float(r0.pvalue) * 3, 1)\n"
                "a1 = min(float(r1.pvalue) * 3, 1)\n"
                "a2 = min(float(r2.pvalue) * 3, 1)\n"
                "print(a0 < 0.05); print(a1 < 0.05); print(a2 < 0.05)"
            )
        ),
    },
    "correct-display-decision-gates-correction": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            after="if r0.pvalue < 0.05:\n    multipletests([r0.pvalue, r1.pvalue, r2.pvalue])\n",
        ),
    },
    "correct-early-return-panel-gate": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _EARLY_RETURN,
    },
    "correct-two-prespecified-families": {
        "expected": "multiple-family-partition-present",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=(
                "first = [r0.pvalue]\nsecond = [r1.pvalue, r2.pvalue]\n"
                "reject_first, _, _, _ = multipletests(first)\n"
                "reject_second, _, _, _ = multipletests(second)\n"
                "print(reject_first[0]); print(reject_second[0]); print(reject_second[1])"
            ),
        ),
    },
    "correct-hand-sidak-threshold": {
        "expected": "unresolved-decision-threshold",
        "source": _explicit(
            decisions="print(r0.pvalue < 1 - (1 - 0.05) ** (1 / 3)); print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
        ),
    },
    "correct-off-registry-pingouin-multicomp": {
        "expected": "unresolved-manual-correction-present",
        "source": _explicit(
            imports="import pingouin\n",
            after="pingouin.multicomp([r0.pvalue, r1.pvalue, r2.pvalue])\n",
        ),
    },
    "correct-default-method-multipletests": {
        "expected": "covered-negative",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=_COMPLETE,
        ),
    },
    "correct-sensitivity-duplicate": {
        "expected": "extra-registered-test-outside-authorized-family",
        "source": _explicit(
            after='stats.ttest_ind(df.loc[df["group"] == "a", "m1"], df.loc[df["group"] == "b", "m1"])\n'
        ),
    },
    "correct-discovery-validation-split": {
        "expected": "test-battery-cardinality-unresolved",
        "source": _explicit(
            after=(
                'selected = [name for name in ["m1", "m2", "m3"] if df[name].mean() > 0]\n'
                "for column in selected:\n"
                '    stats.ttest_ind(df.loc[df["group"] == "a", column], '
                'df.loc[df["group"] == "b", column])\n'
            )
        ),
    },
    "correct-discovery-validation-fixed-count": {
        "expected": "selected-group-row-completeness-unproven",
        "source": _explicit().replace(
            'df.loc[df["group"] == "a", "m1"]',
            'df.loc[(df["group"] == "a") & (df["m2"] > 0), "m1"]',
            1,
        ),
    },
    "correct-numpy-omnibus-assert-gate": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            imports="import numpy as np\n",
            before='gate = np.abs(np.mean(df[["m1", "m2", "m3"]].to_numpy(), axis=0)).sum()\nassert gate > 0\n',
        ),
    },
    "correct-match-guard-and-boolop-gate": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            imports="import numpy as np\n",
            before='gate = np.abs(np.mean(df[["m1", "m2", "m3"]].to_numpy(), axis=0)).sum()\nmatch gate:\n    case value if value > 0 and gate:\n        pass\n',
        ),
    },
    "correct-label-permutation-max-t-resolved": {
        "expected": "permutation-family-control-present",
        "source": _explicit(
            after='null = []\nfor _ in range(20):\n    permuted = df.sample(frac=1)\n    null.append(max(permuted["m1"]))\n'
        ),
    },
    "correct-label-permutation-max-t-unresolved": {
        "expected": "resampling-cardinality-unresolved",
        "source": _explicit(
            after='null = []\nfor _ in range(20 * len(df)):\n    permuted = df.sample(frac=1)\n    null.append(max(permuted["m1"]))\n'
        ),
    },
    "correct-family-extremum": {
        "expected": "family-pvalue-extremum-reduction-present",
        "source": _explicit(
            after="pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\nprint(min(pvalues))\n"
        ),
    },
    "correct-hand-bonferroni-off-ast": {
        "expected": "unresolved-decision-threshold",
        "source": _explicit(
            decisions="print(r0.pvalue < 0.01); print(r1.pvalue < 0.01); print(r2.pvalue < 0.01)"
        ),
    },
    "correct-preregistered-0.01-n4": {
        "expected": "unresolved-decision-threshold",
        "columns": ("m1", "m2", "m3", "m4"),
        "source": _explicit(
            columns=("m1", "m2", "m3", "m4"),
            decisions="print(r0.pvalue < 0.01); print(r1.pvalue < 0.01); print(r2.pvalue < 0.01); print(r3.pvalue < 0.01)",
        ),
    },
    "correct-r12-store-inside-called-helper": {
        "expected": "pderived-conclusion-family-incomplete",
        "source": _explicit(
            decisions=_R12_SEQUENCE + "def overwrite():\n    p = 0.01\n    return p\noverwrite()"
        ),
    },
    "correct-r12-conditional-store": {
        "expected": "pderived-conclusion-family-incomplete",
        "source": _explicit(decisions=_R12_SEQUENCE + "if len(df) > 2:\n    p = 0.01"),
    },
    "correct-r12-loop-carried-store": {
        "expected": "pderived-conclusion-family-incomplete",
        "source": _explicit(decisions=_R12_SEQUENCE + "for marker in [0]:\n    p = 0.01"),
    },
    "correct-r15-unresolved-store-retains-conservative-origins": {
        "expected": "pvalue-family-collection-unresolved",
        "source": _R15_UNRESOLVED_STORE,
    },
    "correct-r5-preregistered-verdict-cutoff-N5": {
        "expected": "unresolved-decision-threshold",
        "columns": ("m1", "m2", "m3", "m4", "m5"),
        "source": _explicit(
            columns=("m1", "m2", "m3", "m4", "m5"),
            decisions=(
                'def verdict(p):\n    return "significant" if p < 0.01 else "not"\n'
                "print(r0.pvalue < 0.05, verdict(r0.pvalue))\n"
                "print(r1.pvalue < 0.05)\nprint(r2.pvalue < 0.05)\n"
                "print(r3.pvalue < 0.05)\nprint(r4.pvalue < 0.05)"
            ),
        ),
    },
    "correct-r3b-different-static-sink-target": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            imports="import sys\n",
            decisions=(
                'if r0.pvalue < 0.05:\n    print("significant")\n'
                'else:\n    print("not", file=sys.stderr)\n'
                "print(r1.pvalue < 0.05)\nprint(r2.pvalue < 0.05)"
            ),
        ),
    },
    "correct-r1-percent-display-plus-hand-holm": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            decisions=(
                "def hand_holm(p):\n    return p * 3\n"
                'print("%s" % hand_holm(r0.pvalue), r0.pvalue < 0.05)\n'
                "print(r1.pvalue < 0.05)\nprint(r2.pvalue < 0.05)"
            )
        ),
    },
    "correct-r2-branch-selects-correction": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            decisions=(
                "pvalues = [r0.pvalue, r1.pvalue, r2.pvalue]\n"
                "if r0.pvalue < 0.05:\n    reject = multipletests(pvalues)[0]\n"
                "else:\n    reject = [False, False, False]\n"
                "print(r0.pvalue < 0.05); print(r1.pvalue < 0.05); "
                "print(r2.pvalue < 0.05)"
            ),
        ),
    },
    "correct-r3b-second-emission-branch": {
        "expected": "hierarchical-gatekeeping-present",
        "source": _explicit(
            decisions=(
                'if r0.pvalue < 0.05:\n    print("significant")\n'
                'else:\n    print("not")\n    print("second branch")\n'
                "print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
            )
        ),
    },
    "correct-r4-record-method-adjusts-p": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            imports="import dataclasses\n",
            decisions=(
                "@dataclasses.dataclass\nclass Result:\n    p: float\n"
                "    def adjusted(self):\n        return self.p * 3\n"
                "record = Result(r0.pvalue)\n"
                "print(record.adjusted(), r0.pvalue < 0.05)\n"
                "print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
            ),
        ),
    },
    "correct-r5-hand-holm-helper": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            decisions=(
                "def hand_holm(p):\n    return p * 3\n"
                "def show(p):\n    return hand_holm(p)\n"
                "print(show(r0.pvalue), r0.pvalue < 0.05)\n"
                "print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
            )
        ),
    },
    "correct-r6-helper-local-bonferroni-threshold": {
        "expected": "unresolved-decision-threshold",
        "corpus_case": "spec-49",
        "source": _SPEC49_R6,
    },
    "correct-r7-helper-returns-unrecognized-adjusted-p": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            decisions=(
                "def adjust(p):\n    return p * 3\n"
                "def package(p):\n    return (f'{p}', adjust(p))\n"
                "text, adjusted = package(r0.pvalue)\n"
                "print(text, adjusted < 0.05)\n"
                "print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
            )
        ),
    },
    "correct-r9-prebound-qc-and-group-mask": {
        "expected": "selected-group-row-completeness-unproven",
        "source": _masked_operands(),
    },
    "correct-r9-mask-sum-does-not-feed-selection": {
        "expected": "covered-negative",
        "source": _explicit(
            imports="from statsmodels.stats.multitest import multipletests\n",
            before='mask = df["group"] == "a"\nprint(mask.sum())\n',
            decisions=_COMPLETE,
        ),
    },
    "correct-r10-dtype-after-validation-filter": {
        "expected": "selected-group-row-completeness-unproven",
        "source": _masked_operands(dtype=".to_numpy(dtype=float)"),
    },
    "correct-r11-while-skips-family-member": {
        "expected": "authorized-family-test-census-incomplete",
        "source": """import pandas as pd
from scipy import stats
OUTCOMES = ["m1", "m2", "m3"]
df = pd.read_csv("data.csv")
index = 0
results = []
while index < len(OUTCOMES):
    if index == 1:
        index += 1
        continue
    column = OUTCOMES[index]
    results.append(stats.ttest_ind(
        df.loc[df["group"] == "a", column],
        df.loc[df["group"] == "b", column],
    ))
    index += 1
print(results)
""",
    },
    "correct-r13-join-through-unknown-adjuster": {
        "expected": "unresolved-pvalue-consumer",
        "source": _explicit(
            decisions=(
                "def adjust(p):\n    return p * 3\n"
                "values = ['%.4f' % adjust(r0.pvalue), '%.4f' % r1.pvalue, "
                "'%.4f' % r2.pvalue]\nprint(', '.join(values))\n"
                "print(r0.pvalue < 0.05); print(r1.pvalue < 0.05); "
                "print(r2.pvalue < 0.05)"
            )
        ),
    },
    "correct-r14-stores-unrecognized-reject": {
        "expected": "unresolved-pvalue-consumer",
        "source": """import pandas as pd
from scipy import stats
from custom import adjust
OUTCOMES = ["m1", "m2", "m3"]
df = pd.read_csv("data.csv")
pvalues = []
records = {}
for column in OUTCOMES:
    a = df.loc[df["group"] == "a", column]
    b = df.loc[df["group"] == "b", column]
    result = stats.ttest_ind(a, b)
    pvalues.append(result.pvalue)
    records[column] = {"p": result.pvalue}
reject = adjust(pvalues)
for index, column in enumerate(OUTCOMES):
    records[column]["decision"] = reject[index] < 0.05
for column in OUTCOMES:
    print(records[column]["p"] < 0.05, records[column]["decision"])
""",
    },
    "correct-r16-complete-correction-two-pass-zip": {
        "expected": "covered-negative",
        "source": _R16_COMPLETE,
    },
    "correct-r16-unknown-zip-argument": {
        "expected": "pderived-conclusion-family-incomplete",
        "source": _R16_COMPLETE.replace(
            "for column, p, q, flag in zip(OUTCOMES, pvalues, adjusted, reject):",
            "import sys\nfor column, p, q, flag, extra in "
            "zip(OUTCOMES, pvalues, adjusted, reject, sys.argv):",
        ),
    },
    "correct-r18-table-index-hand-sidak": {
        "expected": "unresolved-decision-threshold",
        "source": _explicit(
            decisions=(
                "labels = ['significant', 'not']\n"
                "print(labels[int(r0.pvalue < (1 - (1 - 0.05) ** (1 / 3)))])\n"
                "print(r1.pvalue < 0.05); print(r2.pvalue < 0.05)"
            )
        ),
    },
}
