"""Ostrich chick grower trial: compare two rearing diets on eight declared outcomes.

Reads `ostrich_chick_grower_trial.csv` from the project root, compares the standard
grower ration against the lucerne-enriched grower ration on each declared outcome with a
two-sample Welch t-test, and prints group sizes, group means, the test statistic and the
p-value for every outcome, followed by a significance verdict at the conventional 0.05
threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "ostrich_chick_grower_trial.csv"

GROUP_COLUMN = "diet_group"
REFERENCE_GROUP = "standard"
COMPARISON_GROUP = "lucerne_enriched"

ALPHA = 0.05

# The eight outcomes declared in the trial protocol, in the declared order.
DECLARED_OUTCOMES = [
    "body_weight_kg",
    "average_daily_gain_g_per_day",
    "feed_conversion_ratio",
    "tibiotarsus_length_cm",
    "hock_circumference_cm",
    "serum_total_protein_g_per_l",
    "serum_calcium_mmol_per_l",
    "packed_cell_volume_percent",
]


def compare_outcomes(data, outcomes):
    """Run the two-sample test for each declared outcome and collect the results.

    `data` is the trial data frame and `outcomes` is the declared outcome list. Returns a
    list of result dictionaries, one per outcome, in the order the outcomes were declared.
    """
    results = []
    for outcome in outcomes:
        reference = data.loc[data[GROUP_COLUMN] == REFERENCE_GROUP, outcome]
        comparison = data.loc[data[GROUP_COLUMN] == COMPARISON_GROUP, outcome]

        statistic, p_value = stats.ttest_ind(
            comparison, reference, equal_var=False
        )

        results.append(
            {
                "outcome": outcome,
                "n_reference": int(reference.size),
                "n_comparison": int(comparison.size),
                "mean_reference": float(reference.mean()),
                "mean_comparison": float(comparison.mean()),
                "difference": float(comparison.mean() - reference.mean()),
                "statistic": float(statistic),
                "p_value": float(p_value),
            }
        )
    return results


def load_data():
    """Read the trial CSV."""
    return pd.read_csv(DATA_FILE)


def main():
    data = load_data()
    results = compare_outcomes(data, DECLARED_OUTCOMES)

    print("Ostrich chick grower trial: standard vs lucerne-enriched ration")
    print(f"Data file: {DATA_FILE.name}")
    print(f"Rows: {len(data)}")
    print(f"Test: two-sample Welch t-test, two-sided, alpha = {ALPHA}")
    print()

    for result in results:
        print(f"Outcome: {result['outcome']}")
        print(
            f"  n ({REFERENCE_GROUP}) = {result['n_reference']}, "
            f"n ({COMPARISON_GROUP}) = {result['n_comparison']}"
        )
        print(
            f"  mean ({REFERENCE_GROUP}) = {result['mean_reference']:.4f}, "
            f"mean ({COMPARISON_GROUP}) = {result['mean_comparison']:.4f}"
        )
        print(
            f"  difference (lucerne_enriched - standard) = {result['difference']:.4f}"
        )
        print(f"  t = {result['statistic']:.4f}")
        print(f"  p = {result['p_value']:.4f}")
        print()

    print(f"Verdicts at the conventional {ALPHA} threshold")
    print("-" * 60)
    for result in results:
        verdict = (
            "significant difference between diets"
            if result["p_value"] < ALPHA
            else "no significant difference between diets"
        )
        print(f"{result['outcome']}: p = {result['p_value']:.4f} -> {verdict}")


if __name__ == "__main__":
    main()
