"""Irrigation and strawberry fruit quality: analysis of soluble solids content.

The data file holds one row per berry, six berries per mother plant. The mother plant is
the unit that was assigned to an irrigation schedule, so the six berries from a plant are
subsamples and not independent observations. This script therefore reduces the berry-level
table to one value per plant first, in a separate step, and runs the two-group comparison
on the per-plant table only.

Run with:  python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strawberry_brix.csv")

UNIT_COLUMN = "plant_id"
GROUP_COLUMN = "irrigation_schedule"
RESPONSE_COLUMN = "soluble_solids_brix"
GROUP_LEVELS = ("deficit", "full")


def load_berry_table(path=DATA_FILE):
    """Read the berry-level data file exactly as distributed."""
    berries = pd.read_csv(path)
    required = [UNIT_COLUMN, GROUP_COLUMN, "berry_id", RESPONSE_COLUMN,
                "berry_fresh_weight_g", "polytunnel_row"]
    missing = [column for column in required if column not in berries.columns]
    if missing:
        raise ValueError("data file is missing expected columns: %s" % ", ".join(missing))
    return berries


def reduce_to_plant_means(berries):
    """Reduce the berry-level table to one summarised value per mother plant.

    This is the step that moves the analysis from the measurement unit (the berry) to the
    experimental unit (the plant). It takes the full berry-level table and hands back a
    table with one row per plant, carrying that plant's mean soluble solids content and the
    irrigation schedule the plant was assigned to. Everything downstream of this function
    works on plants, never on berries.
    """
    for plant_id, plant_rows in berries.groupby(UNIT_COLUMN):
        schedules = plant_rows[GROUP_COLUMN].unique()
        if len(schedules) != 1:
            raise ValueError(
                "plant %s carries more than one irrigation schedule: %s"
                % (plant_id, ", ".join(sorted(schedules)))
            )

    plants = (
        berries
        .groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            mean_soluble_solids_brix=(RESPONSE_COLUMN, "mean"),
            within_plant_sd_brix=(RESPONSE_COLUMN, "std"),
            n_berries=(RESPONSE_COLUMN, "size"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )
    return plants


def summarise_by_schedule(plants):
    """Per-schedule sample size, mean and standard deviation of the per-plant values."""
    return (
        plants
        .groupby(GROUP_COLUMN)["mean_soluble_solids_brix"]
        .agg(n_plants="size", mean_brix="mean", sd_brix="std")
        .reindex(list(GROUP_LEVELS))
    )


def compare_schedules(plants):
    """Independent two-sample comparison of the per-plant mean soluble solids values.

    Welch's two-sample t-test is used because the two schedules are separate sets of
    plants and their between-plant spreads are not assumed equal. The sample size is the
    number of plants in each group.
    """
    deficit = plants.loc[plants[GROUP_COLUMN] == "deficit", "mean_soluble_solids_brix"]
    full = plants.loc[plants[GROUP_COLUMN] == "full", "mean_soluble_solids_brix"]

    result = stats.ttest_ind(deficit, full, equal_var=False)

    n_deficit = int(deficit.size)
    n_full = int(full.size)
    difference = float(deficit.mean() - full.mean())
    standard_error = float(
        (deficit.var(ddof=1) / n_deficit + full.var(ddof=1) / n_full) ** 0.5
    )
    # Welch-Satterthwaite degrees of freedom.
    df = float(
        (deficit.var(ddof=1) / n_deficit + full.var(ddof=1) / n_full) ** 2
        / (
            (deficit.var(ddof=1) / n_deficit) ** 2 / (n_deficit - 1)
            + (full.var(ddof=1) / n_full) ** 2 / (n_full - 1)
        )
    )
    critical = float(stats.t.ppf(0.975, df))
    ci_low = difference - critical * standard_error
    ci_high = difference + critical * standard_error

    return {
        "n_deficit_plants": n_deficit,
        "n_full_plants": n_full,
        "mean_deficit": float(deficit.mean()),
        "mean_full": float(full.mean()),
        "difference": difference,
        "standard_error": standard_error,
        "t_statistic": float(result.statistic),
        "df": df,
        "p_value": float(result.pvalue),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
    }


def main():
    berries = load_berry_table()
    print("Berry-level data file: %s" % os.path.basename(DATA_FILE))
    print("Berry rows read: %d" % len(berries))
    print("Distinct mother plants: %d" % berries[UNIT_COLUMN].nunique())
    print()

    plants = reduce_to_plant_means(berries)
    print("Per-plant table after reduction: %d rows (one per mother plant)" % len(plants))
    print("Berries contributing to each plant mean: %s"
          % ", ".join(str(value) for value in sorted(plants["n_berries"].unique())))
    print()

    summary = summarise_by_schedule(plants)
    print("Per-schedule summary of per-plant mean soluble solids (degrees Brix)")
    print("  schedule   n_plants   mean    sd")
    for schedule, row in summary.iterrows():
        print("  %-9s  %8d   %5.2f  %5.2f"
              % (schedule, int(row["n_plants"]), row["mean_brix"], row["sd_brix"]))
    print()

    mean_within = plants.groupby(GROUP_COLUMN)["within_plant_sd_brix"].mean().reindex(list(GROUP_LEVELS))
    print("Mean within-plant (berry-to-berry) standard deviation, degrees Brix")
    for schedule, value in mean_within.items():
        print("  %-9s  %5.2f" % (schedule, value))
    print()

    test = compare_schedules(plants)
    print("Welch two-sample t-test on per-plant mean soluble solids")
    print("  unit of analysis: mother plant")
    print("  n = %d deficit plants vs %d full plants (not 144 berries)"
          % (test["n_deficit_plants"], test["n_full_plants"]))
    print("  mean difference (deficit - full) = %+.2f degrees Brix" % test["difference"])
    print("  95%% confidence interval = %.2f to %.2f degrees Brix"
          % (test["ci_low"], test["ci_high"]))
    print("  t = %.3f, df = %.2f, p = %.5f"
          % (test["t_statistic"], test["df"], test["p_value"]))


if __name__ == "__main__":
    main()
