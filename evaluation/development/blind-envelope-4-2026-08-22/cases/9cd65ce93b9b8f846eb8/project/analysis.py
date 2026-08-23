"""Compare adult male wall lizard body size between two offshore islands.

Design. Forty-four lizards were captured, measured and marked once each, 22 per
island. One row of `lizard_svl.csv` is one individual lizard, so the row and the
independent experimental unit are the same thing and no lizard contributes more
than one measurement. The two islands are therefore compared directly with an
independent two-sample comparison of means over the rows of the table.

Outcome: `svl_mm`, snout-to-vent length in millimetres.
Groups: `predator_status`, `snakes_present` versus `snakes_absent`.

Run: python3 analysis.py
"""

import math
import os

import pandas as pd
from scipy import stats

DATA_FILE = "lizard_svl.csv"
UNIT_COLUMN = "lizard_id"
GROUP_COLUMN = "predator_status"
OUTCOME_COLUMN = "svl_mm"
GROUPS = ("snakes_absent", "snakes_present")


def load_data():
    """Read the frozen CSV that ships with the project."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    return pd.read_csv(path)


def check_one_row_per_lizard(frame):
    """Confirm the design assumption that a row is an individual lizard.

    The two-sample test treats every row as an independent observation. That is
    only correct if each lizard appears exactly once and carries exactly one
    group label, so both facts are checked instead of assumed.
    """
    n_rows = len(frame)
    n_lizards = frame[UNIT_COLUMN].nunique()
    if n_rows != n_lizards:
        raise ValueError(
            "expected one row per lizard, found %d rows for %d distinct %s values"
            % (n_rows, n_lizards, UNIT_COLUMN)
        )

    labels_per_lizard = frame.groupby(UNIT_COLUMN)[GROUP_COLUMN].nunique()
    if (labels_per_lizard != 1).any():
        raise ValueError("at least one lizard carries more than one predator status")

    islands_per_lizard = frame.groupby(UNIT_COLUMN)["island"].nunique()
    if (islands_per_lizard != 1).any():
        raise ValueError("at least one lizard is assigned to more than one island")

    missing = frame.isna().sum().sum()
    if missing:
        raise ValueError("expected no missing values, found %d" % missing)

    return n_rows, n_lizards


def describe_groups(frame):
    """Per-island counts, means and standard deviations of the outcome."""
    summary = (
        frame.groupby([GROUP_COLUMN, "island"])[OUTCOME_COLUMN]
        .agg(n="size", mean="mean", sd="std", minimum="min", maximum="max")
        .reset_index()
    )
    return summary


def welch_test(values_absent, values_present):
    """Welch's independent two-sample t-test plus a 95% CI for the difference.

    Welch's version is used rather than the pooled-variance version because it
    does not require the two islands to have equal variances, and it costs
    nothing when they do.
    """
    result = stats.ttest_ind(values_absent, values_present, equal_var=False)

    n_a, n_p = len(values_absent), len(values_present)
    var_a, var_p = values_absent.var(ddof=1), values_present.var(ddof=1)
    se = math.sqrt(var_a / n_a + var_p / n_p)
    df = (var_a / n_a + var_p / n_p) ** 2 / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_p / n_p) ** 2 / (n_p - 1)
    )
    diff = values_absent.mean() - values_present.mean()
    crit = stats.t.ppf(0.975, df)
    ci = (diff - crit * se, diff + crit * se)

    # Pooled standard deviation effect size (Hedges-uncorrected Cohen's d).
    pooled_sd = math.sqrt(
        ((n_a - 1) * var_a + (n_p - 1) * var_p) / (n_a + n_p - 2)
    )
    cohens_d = diff / pooled_sd

    return {
        "t": float(result.statistic),
        "p": float(result.pvalue),
        "df": df,
        "diff": diff,
        "se": se,
        "ci_low": ci[0],
        "ci_high": ci[1],
        "cohens_d": cohens_d,
    }


def main():
    frame = load_data()
    n_rows, n_lizards = check_one_row_per_lizard(frame)

    print("Wall lizard body size: snake island versus snake-free island")
    print("=" * 62)
    print("Rows in CSV:        %d" % n_rows)
    print("Distinct lizards:   %d" % n_lizards)
    print("Rows and individuals are the same thing: each lizard was captured,")
    print("measured and marked once, so every row is a different animal.")
    print()

    summary = describe_groups(frame)
    print("Per-island summary of %s" % OUTCOME_COLUMN)
    print("-" * 62)
    for _, row in summary.iterrows():
        print(
            "%-15s %-14s n=%2d  mean=%6.2f  sd=%5.2f  range=%.1f-%.1f"
            % (
                row["island"],
                row[GROUP_COLUMN],
                row["n"],
                row["mean"],
                row["sd"],
                row["minimum"],
                row["maximum"],
            )
        )
    print()

    values_absent = frame.loc[frame[GROUP_COLUMN] == "snakes_absent", OUTCOME_COLUMN]
    values_present = frame.loc[frame[GROUP_COLUMN] == "snakes_present", OUTCOME_COLUMN]

    stats_out = welch_test(values_absent, values_present)

    print("Independent two-sample comparison (Welch's t-test)")
    print("-" * 62)
    print("n (snakes absent):  %d lizards" % len(values_absent))
    print("n (snakes present): %d lizards" % len(values_present))
    print("n (total):          %d lizards" % (len(values_absent) + len(values_present)))
    print("mean svl, snakes absent:  %.2f mm" % values_absent.mean())
    print("mean svl, snakes present: %.2f mm" % values_present.mean())
    print(
        "difference (absent - present): %.2f mm  (95%% CI %.2f to %.2f)"
        % (stats_out["diff"], stats_out["ci_low"], stats_out["ci_high"])
    )
    print("standard error of difference: %.3f mm" % stats_out["se"])
    print("t = %.4f   df = %.2f   p = %.6f" % (stats_out["t"], stats_out["df"], stats_out["p"]))
    print("Cohen's d = %.3f" % stats_out["cohens_d"])
    print()

    if stats_out["p"] < 0.05:
        direction = "smaller" if stats_out["diff"] > 0 else "larger"
        print(
            "Conclusion: at the 5%% level, lizards are significantly %s on the island"
            % direction
        )
        print("where snakes are present.")
    else:
        print("Conclusion: at the 5% level, the two islands do not differ detectably")
        print("in snout-to-vent length.")


if __name__ == "__main__":
    main()
