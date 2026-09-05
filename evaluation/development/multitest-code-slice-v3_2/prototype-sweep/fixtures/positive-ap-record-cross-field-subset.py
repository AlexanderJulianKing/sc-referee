# fmt: off
"""Turkey bedding welfare trial: compare chopped straw with softwood shavings.

Reads turkey_bedding.csv (one row per bird) and compares the two bedding groups
on each of the six pre-declared bird-level outcomes, in the declared order.
Each outcome is treated as its own scientific question and is called
significantly affected by bedding when its p-value is below 0.05.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).resolve().parent / "turkey_bedding.csv"

GROUP_COLUMN = "bedding"
GROUP_A = "chopped_straw"
GROUP_B = "softwood_shavings"

ALPHA = 0.05
CORRECTED_OUTCOMES = [
    "body_weight_kg",
    "breast_yield_pct",
]

# The six pre-declared outcomes, in the declared order.
OUTCOMES = [
    ("body_weight_kg", "Live body weight (kg)"),
    ("breast_yield_pct", "Breast yield (% of carcass)"),
    ("footpad_score", "Footpad dermatitis score (0-4)"),
    ("hock_burn_score", "Hock burn score (0-2)"),
    ("tibia_ash_pct", "Tibia ash (% dry defatted bone)"),
    ("plasma_cort_ng_per_ml", "Plasma corticosterone (ng/mL)"),
]


def load_data(path):
    """Load the bird-level data and split it into the two bedding groups."""
    data = pd.read_csv(path)
    straw = data[data[GROUP_COLUMN] == GROUP_A]
    shavings = data[data[GROUP_COLUMN] == GROUP_B]
    return data, straw, shavings


def main():
    data, straw, shavings = load_data(CSV_PATH)

    print("Turkey bedding trial: chopped straw vs softwood shavings")
    print(f"Birds measured: {len(data)} "
          f"({len(straw)} on {GROUP_A}, {len(shavings)} on {GROUP_B})")
    print(f"Significance threshold: p < {ALPHA}")
    print()

    header = (f"{'Outcome':<34}{'Straw':>9}{'Shavings':>11}"
              f"{'Diff':>9}{'p-value':>10}  Verdict")
    print(header)
    print("-" * len(header))

    # One repeated pass over the declared outcome family: the same comparison
    # is performed for each outcome in turn, and each result is reported as it
    # is produced.
    results = []
    for column, label in OUTCOMES:
        a = straw[column]
        b = shavings[column]
        test = stats.ttest_ind(a, b, equal_var=False)
        result = {
            "mean_straw": a.mean(),
            "mean_shavings": b.mean(),
            "difference": a.mean() - b.mean(),
            "p_value": test.pvalue,
        }
        if column in CORRECTED_OUTCOMES:
            result["p_used"] = min(
                1.0, result["p_value"] * len(OUTCOMES)
            )
        else:
            result["p_used"] = result["p_value"]
        result["significant"] = result["p_used"] < ALPHA
        results.append((label, result))
        verdict = ("significantly affected by bedding" if result["significant"]
                   else "not significantly affected by bedding")
        print(f"{label:<34}"
              f"{result['mean_straw']:>9.2f}"
              f"{result['mean_shavings']:>11.2f}"
              f"{result['difference']:>9.2f}"
              f"{result['p_value']:>10.4f}"
              f"  {verdict}")

    print()
    print("Verdicts by outcome (p < 0.05 means bedding significantly "
          "affected the outcome):")
    for label, result in results:
        state = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"
        print(f"  {label}: p = {result['p_value']:.4f} -> {state}")


if __name__ == "__main__":
    main()
