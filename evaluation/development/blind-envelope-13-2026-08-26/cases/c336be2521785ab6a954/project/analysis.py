"""Compare two within-row cotton planting densities on six declared outcomes.

Reads cotton_density_plants.csv from the project root, and for each declared
outcome runs the same two-sample significance test (Welch's two-sample t-test)
between the conventional and high density groups, printing group sizes, group
means, the test statistic and the p-value.

Run from the project root:

    python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

CSV_NAME = "cotton_density_plants.csv"
GROUP_COLUMN = "planting_density"
REFERENCE_GROUP = "conventional"
COMPARISON_GROUP = "high"
ALPHA = 0.05

# The pre-declared outcome family, in the order declared in the trial protocol.
DECLARED_OUTCOMES = [
    ("bolls_per_plant", "bolls per plant"),
    ("lint_yield_g", "lint yield (g)"),
    ("upper_half_mean_length_mm", "upper half mean length (mm)"),
    ("micronaire", "micronaire (unitless)"),
    ("plant_height_cm", "plant height (cm)"),
    ("first_fruiting_branch_node", "first fruiting branch node"),
]


def load_data():
    """Load the plant-level measurements from the project root."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    return pd.read_csv(path)


def main():
    data = load_data()

    reference = data[data[GROUP_COLUMN] == REFERENCE_GROUP]
    comparison = data[data[GROUP_COLUMN] == COMPARISON_GROUP]

    print("Cotton planting density comparison")
    print("=" * 78)
    print(f"Data file: {CSV_NAME}")
    print(f"Plants sampled: {len(data)}")
    print(f"Group '{REFERENCE_GROUP}': n = {len(reference)}")
    print(f"Group '{COMPARISON_GROUP}': n = {len(comparison)}")
    print(f"Test: Welch's two-sample t-test, significance threshold alpha = {ALPHA}")
    print("=" * 78)

    # One repeated pass over the declared outcome list, in the declared order.
    for position, (column, label) in enumerate(DECLARED_OUTCOMES, start=1):
        reference_values = reference[column]
        comparison_values = comparison[column]

        reference_mean = reference_values.mean()
        comparison_mean = comparison_values.mean()
        difference = comparison_mean - reference_mean

        t_statistic, p_value = stats.ttest_ind(
            reference_values, comparison_values, equal_var=False
        )

        significant = p_value < ALPHA
        verdict = "SIGNIFICANT" if significant else "not significant"

        print()
        print(f"Declared outcome {position}: {label}  [{column}]")
        print(
            f"  n: {REFERENCE_GROUP} = {len(reference_values)}, "
            f"{COMPARISON_GROUP} = {len(comparison_values)}"
        )
        print(
            f"  mean: {REFERENCE_GROUP} = {reference_mean:.3f}, "
            f"{COMPARISON_GROUP} = {comparison_mean:.3f}"
        )
        print(f"  difference ({COMPARISON_GROUP} - {REFERENCE_GROUP}): {difference:+.3f}")
        print(f"  t = {t_statistic:.4f}")
        print(f"  p = {p_value:.4f}")
        print(f"  verdict at alpha = {ALPHA}: {verdict}")

    print()
    print("=" * 78)
    print("Summary table")
    print(
        f"{'outcome':<30}{'mean_conv':>11}{'mean_high':>11}"
        f"{'t':>10}{'p':>10}  verdict"
    )
    for column, _label in DECLARED_OUTCOMES:
        reference_values = reference[column]
        comparison_values = comparison[column]
        t_statistic, p_value = stats.ttest_ind(
            reference_values, comparison_values, equal_var=False
        )
        verdict = "significant" if p_value < ALPHA else "not significant"
        print(
            f"{column:<30}{reference_values.mean():>11.3f}"
            f"{comparison_values.mean():>11.3f}"
            f"{t_statistic:>10.4f}{p_value:>10.4f}  {verdict}"
        )


if __name__ == "__main__":
    main()
