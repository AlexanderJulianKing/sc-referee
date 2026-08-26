"""Cultivar comparison for the fifth-instar silkworm rearing trial.

Run from the project root:

    python analysis.py

Dependencies (install with pip if missing):

    pandas
    scipy
    pingouin>=0.5

`pingouin` is the specialist third-party statistics package that performs the
multiple-comparison correction. It is not one of the two mainstream
general-purpose scientific/statistical libraries used elsewhere here.
"""

import pandas as pd
from scipy import stats
import pingouin as pg

DATA_FILE = "rearing_trays.csv"
GROUP_COLUMN = "cultivar"
ALPHA = 0.05
CORRECTION_METHOD = "holm"

# The five outcomes declared in the trial protocol, in the declared order.
# They form ONE family; the family-wise error rate is controlled across all
# five together, never outcome by outcome.
OUTCOMES = [
    "mean_cocoon_weight_g",
    "cocoon_shell_ratio_pct",
    "larval_duration_h",
    "silk_filament_length_m",
    "effective_rearing_rate_pct",
]


def main():
    data = pd.read_csv(DATA_FILE)

    groups = sorted(data[GROUP_COLUMN].unique())
    if len(groups) != 2:
        raise ValueError(
            "expected exactly two cultivars, found %r" % (groups,)
        )
    group_a, group_b = groups

    rows_a = data[data[GROUP_COLUMN] == group_a]
    rows_b = data[data[GROUP_COLUMN] == group_b]

    print("Silkworm rearing trial: %s vs %s" % (group_a, group_b))
    print("Data file: %s" % DATA_FILE)
    print("Trays: %d total, %d on %s, %d on %s"
          % (len(data), len(rows_a), group_a, len(rows_b), group_b))
    print("Test for every outcome: two-sample Student t-test "
          "(scipy.stats.ttest_ind, equal variances assumed)")
    print()

    # ---- Stage 1: the same two-sample test on each declared outcome --------
    raw_pvalues = []
    per_outcome = []

    print("Per-outcome comparisons (raw, uncorrected):")
    for outcome in OUTCOMES:
        values_a = rows_a[outcome]
        values_b = rows_b[outcome]

        statistic, pvalue = stats.ttest_ind(values_a, values_b)

        raw_pvalues.append(pvalue)
        per_outcome.append(
            {
                "outcome": outcome,
                "n_a": len(values_a),
                "n_b": len(values_b),
                "mean_a": values_a.mean(),
                "mean_b": values_b.mean(),
                "t": statistic,
                "p_raw": pvalue,
            }
        )

        print("  %s" % outcome)
        print("    n: %s = %d, %s = %d"
              % (group_a, len(values_a), group_b, len(values_b)))
        print("    mean: %s = %.4f, %s = %.4f"
              % (group_a, values_a.mean(), group_b, values_b.mean()))
        print("    t = %.4f, raw p = %.6f" % (statistic, pvalue))
    print()

    # ---- Stage 2: one family-wise correction over all five p-values -------
    # Every verdict below comes from the adjusted p-values returned here.
    # No verdict is read off a raw p-value.
    reject, p_adjusted = pg.multicomp(
        raw_pvalues, alpha=ALPHA, method=CORRECTION_METHOD
    )

    print("Family-wise correction")
    print("  package: pingouin %s (pingouin.multicomp)" % pg.__version__)
    print("  method: %s" % CORRECTION_METHOD)
    print("  family: all %d declared outcomes adjusted together"
          % len(OUTCOMES))
    print("  family-wise alpha: %.2f" % ALPHA)
    print()

    print("Adjusted results (verdicts from adjusted p-values only):")
    header = "%-28s %10s %10s %12s %12s %s" % (
        "outcome", "mean_" + group_a, "mean_" + group_b,
        "p_raw", "p_adj", "verdict",
    )
    print("  " + header)
    for row, p_adj, is_significant in zip(per_outcome, p_adjusted, reject):
        verdict = "significant" if is_significant else "not significant"
        print("  %-28s %10.4f %10.4f %12.6f %12.6f %s"
              % (row["outcome"], row["mean_a"], row["mean_b"],
                 row["p_raw"], p_adj, verdict))

    n_significant = int(sum(bool(flag) for flag in reject))
    print()
    print("Outcomes significant at family-wise alpha %.2f after %s "
          "correction: %d of %d"
          % (ALPHA, CORRECTION_METHOD, n_significant, len(OUTCOMES)))


if __name__ == "__main__":
    main()
