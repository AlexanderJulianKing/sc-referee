"""Compare solar-dryer and open-mat drying of groundnut lots on three declared quality outcomes.

Reads groundnut_drying_quality.csv from the project root, runs the same two-sample
significance test on every declared outcome, and prints group sizes, group means,
the test statistic and the p-value for each outcome.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "groundnut_drying_quality.csv"

GROUP_COLUMN = "drying_method"
SOLAR = "solar_dryer"
MAT = "open_mat"

# The outcome family as declared in the study plan, in the declared order.
DECLARED_OUTCOMES = [
    ("moisture_content_percent_wb", "moisture content", "% wet basis"),
    ("aflatoxin_b1_ug_per_kg", "aflatoxin B1", "ug/kg"),
    ("free_fatty_acids_percent_oleic", "free fatty acids", "% as oleic acid"),
]

ALPHA = 0.05


def compare(frame, column):
    """Two-sample t-test for one outcome column: solar dryer versus open mat."""
    solar = frame.loc[frame[GROUP_COLUMN] == SOLAR, column]
    mat = frame.loc[frame[GROUP_COLUMN] == MAT, column]
    statistic, p_value = stats.ttest_ind(solar, mat)
    return {
        "n_solar": int(solar.size),
        "n_mat": int(mat.size),
        "mean_solar": float(solar.mean()),
        "mean_mat": float(mat.mean()),
        "difference": float(solar.mean() - mat.mean()),
        "statistic": float(statistic),
        "p_value": float(p_value),
    }


def main():
    data = pd.read_csv(DATA_FILE)

    # Build the whole per-outcome collection in one go over the declared outcome list.
    results = {column: compare(data, column) for column, _label, _unit in DECLARED_OUTCOMES}

    print(f"Data file: {DATA_FILE.name}")
    print(f"Lots: {len(data)}")
    print(f"Test: two-sample t-test, {SOLAR} versus {MAT}")
    print(f"Significance threshold: alpha = {ALPHA}")
    print()

    for column, label, unit in DECLARED_OUTCOMES:
        result = results[column]
        # Read the verdict off the collection built above.
        significant = result["p_value"] < ALPHA
        verdict = "SIGNIFICANT" if significant else "NOT SIGNIFICANT"

        print(f"{label} ({column}), unit: {unit}")
        print(f"  n: {SOLAR} = {result['n_solar']}, {MAT} = {result['n_mat']}")
        print(f"  mean {SOLAR}: {result['mean_solar']:.3f}")
        print(f"  mean {MAT}:    {result['mean_mat']:.3f}")
        print(f"  difference (solar - mat): {result['difference']:+.3f}")
        print(f"  t statistic: {result['statistic']:.4f}")
        print(f"  p-value: {result['p_value']:.4f}")
        print(f"  verdict at alpha = {ALPHA}: {verdict}")
        print()

    print("Summary of verdicts")
    for column, label, _unit in DECLARED_OUTCOMES:
        result = results[column]
        verdict = "significant" if result["p_value"] < ALPHA else "not significant"
        print(f"  {label}: p = {result['p_value']:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
