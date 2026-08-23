"""Analysis for the dietary nitrate sprint-power study.

Design and the analysis it forces
---------------------------------
Eighteen trained cyclists were randomised to a dietary nitrate supplement (9) or
a matched placebo (9). Each rider performed five maximal seated sprints in one
session, so the raw file `sprint_power.csv` holds 90 rows: one row per sprint,
five rows per rider.

The rider is the independent experimental unit. Randomisation was applied to the
rider, and the five sprints are repeated efforts by the same person at successive
time points in one session, so those five rows are not independent of one
another. Treating the 90 sprint rows as 90 independent observations would count
each rider five times and understate the standard error.

This script therefore does the reduction first: every rider's five sprints are
collapsed to that rider's mean peak power, giving one value per rider and 18
values in total. The two groups are then compared with an independent
two-sample t-test on those 18 rider-level values, with the sample size being 9
riders per group. Welch's form of the test is used, so equal variance between
the two groups is not assumed. Student's equal-variance t-test is also reported
as a sensitivity check; it is not the primary result.

Nothing is written back to the raw CSV. The reduction happens here, in memory.

Run with: python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "sprint_power.csv")

UNIT_COLUMN = "rider_id"          # the independent experimental unit
GROUP_COLUMN = "supplement_group"
OUTCOME_COLUMN = "peak_power_w"
REPEAT_COLUMN = "sprint_number"
GROUP_ORDER = ["supplement", "placebo"]


def load_raw():
    """Read the raw sprint-level table and check its expected shape."""
    raw = pd.read_csv(DATA_CSV)

    expected_columns = [
        "rider_id",
        "supplement_group",
        "sprint_number",
        "peak_power_w",
        "body_mass_kg",
        "cadence_rpm",
    ]
    missing = [c for c in expected_columns if c not in raw.columns]
    if missing:
        raise ValueError("raw file is missing columns: %s" % missing)

    # Every rider must carry exactly one group label, or the reduction below
    # would be comparing something other than randomised arms.
    groups_per_rider = raw.groupby(UNIT_COLUMN)[GROUP_COLUMN].nunique()
    if (groups_per_rider != 1).any():
        raise ValueError("some rider carries more than one supplement_group label")

    return raw


def reduce_to_one_value_per_rider(raw):
    """Collapse each rider's five sprints to that rider's mean peak power.

    Returns one row per rider. This is the step that makes the later test an
    independent two-sample comparison: after it, each row is one randomised
    unit.
    """
    per_rider = (
        raw.groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            n_sprints=(REPEAT_COLUMN, "count"),
            mean_peak_power_w=(OUTCOME_COLUMN, "mean"),
            body_mass_kg=("body_mass_kg", "first"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )
    return per_rider


def describe_group(values):
    return {
        "n_riders": int(values.size),
        "mean_w": float(values.mean()),
        "sd_w": float(values.std(ddof=1)),
        "min_w": float(values.min()),
        "max_w": float(values.max()),
    }


def main():
    raw = load_raw()

    print("=" * 72)
    print("RAW FILE (as collected, unchanged)")
    print("=" * 72)
    print("rows (sprints)          : %d" % len(raw))
    print("riders                  : %d" % raw[UNIT_COLUMN].nunique())
    print("sprints per rider       : %s"
          % sorted(raw.groupby(UNIT_COLUMN).size().unique().tolist()))
    print("rows are NOT independent: five rows per rider are repeated efforts")
    print()

    per_rider = reduce_to_one_value_per_rider(raw)

    print("=" * 72)
    print("REDUCTION: five sprints -> one value per rider (mean peak power)")
    print("=" * 72)
    print("rider-level rows        : %d" % len(per_rider))
    print()
    with pd.option_context("display.width", 100):
        print(
            per_rider[
                [UNIT_COLUMN, GROUP_COLUMN, "n_sprints", "mean_peak_power_w"]
            ].to_string(index=False, float_format=lambda v: "%.2f" % v)
        )
    print()

    supplement = per_rider.loc[
        per_rider[GROUP_COLUMN] == "supplement", "mean_peak_power_w"
    ].to_numpy()
    placebo = per_rider.loc[
        per_rider[GROUP_COLUMN] == "placebo", "mean_peak_power_w"
    ].to_numpy()

    stats_by_group = {
        "supplement": describe_group(pd.Series(supplement)),
        "placebo": describe_group(pd.Series(placebo)),
    }

    print("=" * 72)
    print("GROUP SUMMARIES (unit of analysis = rider)")
    print("=" * 72)
    print("%-12s %8s %12s %10s %10s %10s"
          % ("group", "n_riders", "mean_w", "sd_w", "min_w", "max_w"))
    for name in GROUP_ORDER:
        s = stats_by_group[name]
        print("%-12s %8d %12.2f %10.2f %10.2f %10.2f"
              % (name, s["n_riders"], s["mean_w"], s["sd_w"],
                 s["min_w"], s["max_w"]))
    print()

    difference_w = stats_by_group["supplement"]["mean_w"] - stats_by_group["placebo"]["mean_w"]

    # Primary test: Welch's independent two-sample t-test on the 18 rider means.
    welch = stats.ttest_ind(supplement, placebo, equal_var=False)
    # Sensitivity check only: Student's equal-variance form.
    student = stats.ttest_ind(supplement, placebo, equal_var=True)

    # Welch confidence interval for the difference in means.
    n1, n2 = supplement.size, placebo.size
    v1 = supplement.var(ddof=1)
    v2 = placebo.var(ddof=1)
    se_diff = (v1 / n1 + v2 / n2) ** 0.5
    welch_df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    t_crit = stats.t.ppf(0.975, welch_df)
    ci_low = difference_w - t_crit * se_diff
    ci_high = difference_w + t_crit * se_diff

    # Hedges' g (small-sample-corrected standardised difference).
    pooled_sd = (((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)) ** 0.5
    cohens_d = difference_w / pooled_sd
    correction = 1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0)
    hedges_g = cohens_d * correction

    print("=" * 72)
    print("PRIMARY TEST: independent two-sample t-test (Welch), rider means")
    print("=" * 72)
    print("sample size             : %d riders in supplement, %d in placebo (18 total)"
          % (n1, n2))
    print("                          (NOT 90 sprints)")
    print("mean difference (W)     : %+.2f  (supplement minus placebo)" % difference_w)
    print("95%% CI for difference   : [%.2f, %.2f] W" % (ci_low, ci_high))
    print("t statistic             : %.4f" % welch.statistic)
    print("degrees of freedom      : %.3f" % welch_df)
    print("p-value (two-sided)     : %.4f" % welch.pvalue)
    print("Hedges' g               : %.3f" % hedges_g)
    print()

    print("-" * 72)
    print("Sensitivity check (not the primary result)")
    print("-" * 72)
    print("Student equal-variance t: t = %.4f, df = %d, p = %.4f"
          % (student.statistic, n1 + n2 - 2, student.pvalue))
    print()

    alpha = 0.05
    print("=" * 72)
    print("INTERPRETATION")
    print("=" * 72)
    if welch.pvalue < alpha:
        verdict = (
            "At alpha = 0.05 the difference between the two groups is "
            "statistically significant."
        )
    else:
        verdict = (
            "At alpha = 0.05 the difference between the two groups is NOT "
            "statistically significant."
        )
    print(verdict)
    print(
        "The supplement group's rider mean peak power was %.1f W %s than the "
        "placebo group's (%.1f W vs %.1f W)."
        % (
            abs(difference_w),
            "higher" if difference_w > 0 else "lower",
            stats_by_group["supplement"]["mean_w"],
            stats_by_group["placebo"]["mean_w"],
        )
    )
    print(
        "With 9 riders per group the study is small, so the confidence interval "
        "is wide and the estimate is imprecise."
    )
    print()
    print("These are simulated data. See DATA_DESCRIPTION.md: no cyclist was")
    print("tested, so this result says nothing about dietary nitrate in reality.")


if __name__ == "__main__":
    main()
