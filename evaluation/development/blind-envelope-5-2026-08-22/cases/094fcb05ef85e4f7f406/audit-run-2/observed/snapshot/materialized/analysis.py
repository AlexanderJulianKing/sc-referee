"""Grazing rotation trial: standing herbage mass on upland sheep pasture.

The paddock is the experimental unit. Rotation was assigned to whole fenced
paddocks, and the ten grid points inside a paddock are subsamples of that same
fenced area, not independent replicates. The analysis therefore runs in two
clearly separated steps:

    step 1  aggregate_to_paddocks()  -- reduce the 160 grid points to one value
                                        per paddock and hand back that table
    step 2  compare_rotations()      -- independent two-sample test of the
                                        difference in means on the returned
                                        per-paddock table

Sample size for the test is the number of paddocks. The number of grid points
is reported only as a description of the sampling effort.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herbage_mass.csv")

UNIT_COL = "paddock_name"
GROUP_COL = "rotation"
POINT_COL = "grid_point"
OUTCOME_COL = "herbage_kg_dm_ha"
HEIGHT_COL = "sward_height_cm"
GROUPS = ("fast_rotation", "set_stocking")


def load_points(path=DATA_FILE):
    """Read the point-level data file. One row is one grid sampling point."""
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Step 1: reduction to the experimental unit
# ---------------------------------------------------------------------------
def aggregate_to_paddocks(points):
    """Reduce grid points to one row per paddock and return that table.

    Each paddock contributes ten grid points. Those points are subsamples, so
    they are averaged into a single paddock-level value before any test. The
    returned table has one row per paddock and is the only table the test sees.
    """
    paddocks = (
        points.groupby([UNIT_COL, GROUP_COL], as_index=False)
        .agg(
            n_grid_points=(POINT_COL, "count"),
            mean_sward_height_cm=(HEIGHT_COL, "mean"),
            mean_herbage_kg_dm_ha=(OUTCOME_COL, "mean"),
            sd_within_paddock=(OUTCOME_COL, "std"),
        )
        .sort_values([GROUP_COL, UNIT_COL], ignore_index=True)
    )
    return paddocks


# ---------------------------------------------------------------------------
# Step 2: the test, on the aggregated table only
# ---------------------------------------------------------------------------
def compare_rotations(paddocks):
    """Independent two-sample test of the difference in mean herbage mass.

    Operates on the per-paddock table returned by aggregate_to_paddocks(), so
    one paddock contributes one observation. Welch's t-test is used: it is the
    independent two-sample t-test without the assumption that the two groups
    share a variance.
    """
    fast = paddocks.loc[paddocks[GROUP_COL] == "fast_rotation", "mean_herbage_kg_dm_ha"]
    set_stocked = paddocks.loc[paddocks[GROUP_COL] == "set_stocking", "mean_herbage_kg_dm_ha"]

    result = stats.ttest_ind(fast, set_stocked, equal_var=False)

    summary = {
        "n_paddocks_fast_rotation": int(fast.size),
        "n_paddocks_set_stocking": int(set_stocked.size),
        "n_paddocks_total": int(fast.size + set_stocked.size),
        "mean_fast_rotation": float(fast.mean()),
        "mean_set_stocking": float(set_stocked.mean()),
        "sd_fast_rotation": float(fast.std(ddof=1)),
        "sd_set_stocking": float(set_stocked.std(ddof=1)),
        "difference_fast_minus_set": float(fast.mean() - set_stocked.mean()),
        "t_statistic": float(result.statistic),
        "df_welch": float(_welch_df(fast, set_stocked)),
        "p_value": float(result.pvalue),
    }
    return summary


def _welch_df(a, b):
    """Welch-Satterthwaite degrees of freedom for the two-sample comparison."""
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = a.size, b.size
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    return num / den


def main():
    points = load_points()

    print("=" * 72)
    print("Grazing rotation trial: standing herbage mass (kg DM/ha)")
    print("=" * 72)

    print("\nSampling effort (description only, not the sample size)")
    print("-" * 72)
    print(f"  Rows (grid sampling points) in the file : {len(points)}")
    print(f"  Distinct paddocks                       : {points[UNIT_COL].nunique()}")
    print(f"  Grid points per paddock                 : "
          f"{points.groupby(UNIT_COL)[POINT_COL].count().unique().tolist()}")
    print(f"  Missing values                          : {int(points.isna().sum().sum())}")

    # Step 1 -----------------------------------------------------------------
    paddocks = aggregate_to_paddocks(points)

    print("\nStep 1. Per-paddock table (the experimental units)")
    print("-" * 72)
    with pd.option_context("display.width", 120, "display.max_columns", 20):
        print(paddocks.round(1).to_string(index=False))

    # Step 2 -----------------------------------------------------------------
    res = compare_rotations(paddocks)

    print("\nStep 2. Independent two-sample test on the per-paddock table")
    print("-" * 72)
    print(f"  Test                       : Welch's independent two-sample t-test")
    print(f"  Unit of analysis           : paddock")
    print(f"  n (paddocks, fast_rotation): {res['n_paddocks_fast_rotation']}")
    print(f"  n (paddocks, set_stocking) : {res['n_paddocks_set_stocking']}")
    print(f"  n (paddocks, total)        : {res['n_paddocks_total']}")
    print()
    print(f"  fast_rotation  mean = {res['mean_fast_rotation']:.1f} kg DM/ha, "
          f"SD = {res['sd_fast_rotation']:.1f} (between paddocks)")
    print(f"  set_stocking   mean = {res['mean_set_stocking']:.1f} kg DM/ha, "
          f"SD = {res['sd_set_stocking']:.1f} (between paddocks)")
    print(f"  difference (fast - set)    : {res['difference_fast_minus_set']:.1f} kg DM/ha")
    print()
    print(f"  t = {res['t_statistic']:.3f}, df = {res['df_welch']:.2f}, "
          f"p = {res['p_value']:.6f}")

    print("\nGroup spread of the raw grid points (description only)")
    print("-" * 72)
    for group in GROUPS:
        sub = points.loc[points[GROUP_COL] == group, OUTCOME_COL]
        print(f"  {group:<14}: {len(sub)} points, "
              f"min {sub.min()}, max {sub.max()}, mean {sub.mean():.1f}")

    print()


if __name__ == "__main__":
    main()
