"""Sourdough starter maturation: does flour type change starter pH?

Reads the frozen bench file `starter_ph_readings.csv` and compares starter pH
between the two flours with a standard independent two-sample t-test, pooling
all six maturation days and treating every daily pH reading as one observation.
"""

import pandas as pd
from scipy import stats

CSV_PATH = "starter_ph_readings.csv"
RYE = "wholemeal_rye"
WHEAT = "refined_white_wheat"


def load_readings(path=CSV_PATH):
    """Load the daily pH readings from the frozen CSV."""
    readings = pd.read_csv(path)
    expected = {"jar_id", "flour_type", "maturation_day", "starter_ph"}
    missing = expected - set(readings.columns)
    if missing:
        raise ValueError(f"missing expected columns: {sorted(missing)}")
    return readings


def describe_groups(readings):
    """Group means, standard deviations, and reading counts for each flour."""
    summary = (
        readings.groupby("flour_type")["starter_ph"]
        .agg(n_readings="count", mean_ph="mean", sd_ph="std")
        .reindex([RYE, WHEAT])
    )
    return summary


def compare_flours(readings):
    """Independent two-sample t-test on starter pH, all daily readings pooled."""
    rye_ph = readings.loc[readings["flour_type"] == RYE, "starter_ph"]
    wheat_ph = readings.loc[readings["flour_type"] == WHEAT, "starter_ph"]
    t_stat, p_value = stats.ttest_ind(rye_ph, wheat_ph)
    return {
        "n_rye": int(rye_ph.size),
        "n_wheat": int(wheat_ph.size),
        "mean_rye": float(rye_ph.mean()),
        "mean_wheat": float(wheat_ph.mean()),
        "sd_rye": float(rye_ph.std(ddof=1)),
        "sd_wheat": float(wheat_ph.std(ddof=1)),
        "mean_difference": float(rye_ph.mean() - wheat_ph.mean()),
        "t_statistic": float(t_stat),
        "df": int(rye_ph.size + wheat_ph.size - 2),
        "p_value": float(p_value),
    }


def main():
    readings = load_readings()

    print(f"rows read: {len(readings)}")
    print(f"jars: {readings['jar_id'].nunique()}")
    print(f"maturation days: {sorted(readings['maturation_day'].unique())}")
    print()

    print("Group summary (all daily readings pooled)")
    print(describe_groups(readings).round(4).to_string())
    print()

    result = compare_flours(readings)
    print("Independent two-sample t-test on starter_ph")
    print(f"  wholemeal rye:        n = {result['n_rye']} readings, "
          f"mean pH = {result['mean_rye']:.3f}, SD = {result['sd_rye']:.3f}")
    print(f"  refined white wheat:  n = {result['n_wheat']} readings, "
          f"mean pH = {result['mean_wheat']:.3f}, SD = {result['sd_wheat']:.3f}")
    print(f"  mean difference (rye - wheat) = {result['mean_difference']:.3f} pH units")
    print(f"  t({result['df']}) = {result['t_statistic']:.4f}, "
          f"p = {result['p_value']:.6g}")


if __name__ == "__main__":
    main()
