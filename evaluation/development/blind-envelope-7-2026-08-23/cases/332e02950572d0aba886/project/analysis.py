"""Harvest-weight comparison for the fermented soy by-product grow-out trial.

Loads the committed harvest table and compares individual shrimp body weight at
harvest between the standard commercial diet and the supplemented diet with an
independent two-sample t-test.

Usage: python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harvest_weights.csv")

STANDARD = "standard"
SUPPLEMENTED = "supplemented"


def load_harvest_table(path=DATA_PATH):
    """Read the committed harvest weights as they were recorded."""
    table = pd.read_csv(path)
    expected = ["pond_id", "feed_treatment", "shrimp_id", "body_weight_g"]
    missing = [name for name in expected if name not in table.columns]
    if missing:
        raise ValueError("harvest table is missing columns: %s" % ", ".join(missing))
    return table


def group_summary(weights):
    """Sample size, mean and standard deviation for one feed treatment."""
    return {
        "n": int(weights.size),
        "mean": float(weights.mean()),
        "sd": float(weights.std(ddof=1)),
    }


def main():
    table = load_harvest_table()

    standard_weights = table.loc[table["feed_treatment"] == STANDARD, "body_weight_g"]
    supplemented_weights = table.loc[table["feed_treatment"] == SUPPLEMENTED, "body_weight_g"]

    standard = group_summary(standard_weights)
    supplemented = group_summary(supplemented_weights)

    t_statistic, p_value = stats.ttest_ind(supplemented_weights, standard_weights)
    degrees_of_freedom = standard["n"] + supplemented["n"] - 2
    difference = supplemented["mean"] - standard["mean"]

    print("Harvest weight by feed treatment")
    print("--------------------------------")
    print("shrimp weighed in file: %d" % len(table))
    print("ponds in file: %d" % table["pond_id"].nunique())
    print("")
    print("%-14s %5s %10s %10s" % ("feed_treatment", "n", "mean_g", "sd_g"))
    print("%-14s %5d %10.2f %10.2f" % (STANDARD, standard["n"], standard["mean"], standard["sd"]))
    print(
        "%-14s %5d %10.2f %10.2f"
        % (SUPPLEMENTED, supplemented["n"], supplemented["mean"], supplemented["sd"])
    )
    print("")
    print("difference (supplemented - standard): %.2f g" % difference)
    print("independent two-sample t-test on individual harvest weights")
    print("t = %.4f, df = %d, p = %.6g" % (t_statistic, degrees_of_freedom, p_value))


if __name__ == "__main__":
    main()
