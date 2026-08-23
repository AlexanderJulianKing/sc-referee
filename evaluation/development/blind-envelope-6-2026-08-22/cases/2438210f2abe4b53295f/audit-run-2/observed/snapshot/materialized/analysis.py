"""Dietary calcium and snail live weight: enclosure-level two-group comparison.

Design recap
------------
Fourteen outdoor mesh enclosures were stocked at equal density. Seven enclosures
received the standard feed and seven received feed with added calcium carbonate.
Feed was assigned to the *enclosure*, not to the individual snail, so the
enclosure is the independent experimental unit. Twenty snails were weighed in
each enclosure; those twenty rows are repeated measurements from one unit, not
twenty independent replicates.

The script is organised as three separate steps:

    1. ``load_snail_rows``  - reads the snail-level CSV and checks its shape.
    2. ``aggregate_to_enclosures`` - collapses snails to one row per enclosure
       and returns that aggregated table.
    3. ``compare_groups`` - runs the independent two-sample test on the
       aggregated table returned by step 2.

Step 2 is the only place where per-enclosure aggregation happens, and step 3
never sees the snail-level rows. No inferential test is run on individual snail
rows anywhere in this script.
"""

import math
import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "snail_weights.csv")

RESPONSE = "live_weight_g"
UNIT_COLUMN = "enclosure_ref"
GROUP_COLUMN = "calcium_level"
GROUP_ORDER = ["standard", "added_calcium"]

EXPECTED_COLUMNS = [
    "enclosure_ref",
    "calcium_level",
    "snail_no",
    "live_weight_g",
    "shell_diameter_mm",
]


# ---------------------------------------------------------------------------
# Step 1: read the snail-level file. This step does no aggregation and no
# testing; it only produces the raw table of weighed snails.
# ---------------------------------------------------------------------------
def load_snail_rows(path=DATA_PATH):
    """Read the snail-level CSV. One returned row is one weighed snail."""
    snails = pd.read_csv(path)

    missing = [c for c in EXPECTED_COLUMNS if c not in snails.columns]
    if missing:
        raise ValueError("snail file is missing columns: {}".format(missing))
    if snails[EXPECTED_COLUMNS].isna().any().any():
        raise ValueError("snail file contains missing values")

    bad_levels = set(snails[GROUP_COLUMN].unique()) - set(GROUP_ORDER)
    if bad_levels:
        raise ValueError("unexpected feed groups: {}".format(sorted(bad_levels)))

    # Feed was assigned to the enclosure, so each enclosure must sit in
    # exactly one feed group.
    groups_per_enclosure = snails.groupby(UNIT_COLUMN)[GROUP_COLUMN].nunique()
    if (groups_per_enclosure != 1).any():
        raise ValueError("an enclosure carries more than one feed group")

    return snails


# ---------------------------------------------------------------------------
# Step 2: aggregate snails to enclosures. This is the unit-of-replication step.
# It is deliberately separate from reading (step 1) and from testing (step 3),
# and it hands back the aggregated table that the test will use.
# ---------------------------------------------------------------------------
def aggregate_to_enclosures(snails):
    """Collapse the snail-level table to one row per enclosure.

    Returns a table with one row per enclosure holding:
        enclosure_ref       - the enclosure identifier
        calcium_level       - the feed group that enclosure received
        mean_live_weight_g  - mean live weight of the snails from that enclosure
        n_snails            - how many snails that enclosure contributed
    """
    enclosures = (
        snails.groupby([UNIT_COLUMN, GROUP_COLUMN], as_index=False)
        .agg(
            mean_live_weight_g=(RESPONSE, "mean"),
            n_snails=(RESPONSE, "size"),
        )
        .sort_values(UNIT_COLUMN)
        .reset_index(drop=True)
    )

    if enclosures[UNIT_COLUMN].duplicated().any():
        raise ValueError("aggregation did not produce one row per enclosure")

    return enclosures


# ---------------------------------------------------------------------------
# Step 3: the two-group comparison. It takes the aggregated enclosure table
# only. It never touches the snail-level rows.
# ---------------------------------------------------------------------------
def compare_groups(enclosures):
    """Independent two-sample t-test on enclosure means (Welch's version).

    The rows of ``enclosures`` are the independent units, so the sample size of
    each group is the number of enclosures in that group.
    """
    standard = enclosures.loc[
        enclosures[GROUP_COLUMN] == "standard", "mean_live_weight_g"
    ].to_numpy()
    added = enclosures.loc[
        enclosures[GROUP_COLUMN] == "added_calcium", "mean_live_weight_g"
    ].to_numpy()

    n_standard = int(standard.size)
    n_added = int(added.size)

    # Welch's independent two-sample t-test: two separate groups of enclosures,
    # no assumption that the two groups share a variance.
    t_stat, p_value = stats.ttest_ind(added, standard, equal_var=False)

    mean_standard = float(standard.mean())
    mean_added = float(added.mean())
    sd_standard = float(standard.std(ddof=1))
    sd_added = float(added.std(ddof=1))
    difference = mean_added - mean_standard

    se_difference = math.sqrt(
        sd_added ** 2 / n_added + sd_standard ** 2 / n_standard
    )
    # Welch-Satterthwaite degrees of freedom.
    df = (sd_added ** 2 / n_added + sd_standard ** 2 / n_standard) ** 2 / (
        (sd_added ** 2 / n_added) ** 2 / (n_added - 1)
        + (sd_standard ** 2 / n_standard) ** 2 / (n_standard - 1)
    )
    t_crit = float(stats.t.ppf(0.975, df))
    ci_low = difference - t_crit * se_difference
    ci_high = difference + t_crit * se_difference

    return {
        "test": "Welch's independent two-sample t-test on enclosure means",
        "unit_of_analysis": "enclosure",
        "n_enclosures_standard": n_standard,
        "n_enclosures_added_calcium": n_added,
        "n_enclosures_total": n_standard + n_added,
        "mean_standard_g": mean_standard,
        "mean_added_calcium_g": mean_added,
        "sd_standard_g": sd_standard,
        "sd_added_calcium_g": sd_added,
        "difference_g": difference,
        "se_difference_g": se_difference,
        "ci95_low_g": ci_low,
        "ci95_high_g": ci_high,
        "t_statistic": float(t_stat),
        "df": float(df),
        "p_value": float(p_value),
    }


def main():
    snails = load_snail_rows()
    enclosures = aggregate_to_enclosures(snails)
    result = compare_groups(enclosures)

    print("Snail-level file")
    print("  rows (weighed snails): {}".format(len(snails)))
    print("  enclosures: {}".format(snails[UNIT_COLUMN].nunique()))
    print(
        "  snails per enclosure: {}".format(
            sorted(snails.groupby(UNIT_COLUMN).size().unique().tolist())
        )
    )
    print()

    print("Aggregated enclosure table (one row per enclosure)")
    printable = enclosures.copy()
    printable["mean_live_weight_g"] = printable["mean_live_weight_g"].round(3)
    print(printable.to_string(index=False))
    print()

    print("Two-group comparison")
    print("  test: {}".format(result["test"]))
    print("  unit of analysis: {}".format(result["unit_of_analysis"]))
    print(
        "  sample size: {} enclosures ({} standard, {} added calcium)".format(
            result["n_enclosures_total"],
            result["n_enclosures_standard"],
            result["n_enclosures_added_calcium"],
        )
    )
    print(
        "  standard feed: mean {:.3f} g, SD {:.3f} g".format(
            result["mean_standard_g"], result["sd_standard_g"]
        )
    )
    print(
        "  added calcium: mean {:.3f} g, SD {:.3f} g".format(
            result["mean_added_calcium_g"], result["sd_added_calcium_g"]
        )
    )
    print(
        "  difference (added calcium - standard): {:.3f} g".format(
            result["difference_g"]
        )
    )
    print(
        "  95% CI for the difference: {:.3f} g to {:.3f} g".format(
            result["ci95_low_g"], result["ci95_high_g"]
        )
    )
    print(
        "  t = {:.3f}, df = {:.2f}, p = {:.5f}".format(
            result["t_statistic"], result["df"], result["p_value"]
        )
    )

    return result


if __name__ == "__main__":
    main()
