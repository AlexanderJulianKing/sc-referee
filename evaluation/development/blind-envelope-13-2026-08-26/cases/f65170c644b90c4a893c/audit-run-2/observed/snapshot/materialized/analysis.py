"""Gari fermentation study: compare back-slopped and spontaneous fermentation.

Reads gari_fermentation_batches.csv from the project root and compares the two
fermentation treatments on the four outcomes declared in the study plan, in the
declared order. The same test (Welch's two-sample t-test) is used for every
outcome. The four outcomes are one declared family, so the family-wise error
rate is controlled with a Sidak per-comparison threshold computed here.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).resolve().parent / "gari_fermentation_batches.csv"

GROUP_COLUMN = "fermentation_treatment"
GROUP_A = "back_slopped"
GROUP_B = "spontaneous"

# The four outcomes declared in the study plan, in the declared order.
DECLARED_OUTCOMES = [
    "total_cyanogenic_potential_mg_hcn_eq_per_kg_dw",
    "ph_72h_ph_units",
    "titratable_acidity_percent_lactic_acid",
    "moisture_content_percent",
]

FAMILY_WISE_ALPHA = 0.05


def sidak_threshold(family_wise_alpha, family_size):
    """Per-comparison threshold: 1 - (1 - alpha_family) ** (1 / family_size)."""
    return 1.0 - (1.0 - family_wise_alpha) ** (1.0 / family_size)


def main():
    data = pd.read_csv(CSV_PATH)

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    # Family size is the number of declared outcomes tested together.
    family_size = len(DECLARED_OUTCOMES)
    per_comparison_alpha = sidak_threshold(FAMILY_WISE_ALPHA, family_size)

    print("Gari fermentation study: back-slopped vs spontaneous")
    print(f"Data file: {CSV_PATH.name}")
    print(f"Rows read: {len(data)}")
    print()
    print("Multiple-comparison control (Sidak)")
    print(f"  family size (number of declared outcomes) = {family_size}")
    print(f"  family-wise level alpha_FW               = {FAMILY_WISE_ALPHA}")
    print(
        f"  Sidak per-comparison threshold            = "
        f"1 - (1 - {FAMILY_WISE_ALPHA}) ** (1 / {family_size}) = "
        f"{per_comparison_alpha:.6f}"
    )
    print()
    print("Test used for every outcome: Welch's two-sample t-test (two-sided)")
    print()

    for position, outcome in enumerate(DECLARED_OUTCOMES, start=1):
        values_a = group_a[outcome]
        values_b = group_b[outcome]

        statistic, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)

        significant = p_value < per_comparison_alpha
        verdict = (
            "significant at the Sidak threshold"
            if significant
            else "not significant at the Sidak threshold"
        )

        print(f"Outcome {position}: {outcome}")
        print(f"  n ({GROUP_A})    = {len(values_a)}")
        print(f"  n ({GROUP_B})    = {len(values_b)}")
        print(f"  mean ({GROUP_A}) = {values_a.mean():.4f}")
        print(f"  mean ({GROUP_B}) = {values_b.mean():.4f}")
        print(f"  difference (back_slopped - spontaneous) = "
              f"{values_a.mean() - values_b.mean():.4f}")
        print(f"  t statistic = {statistic:.4f}")
        print(f"  p-value     = {p_value:.6g}")
        print(f"  verdict     = {verdict} "
              f"(p {'<' if significant else '>='} {per_comparison_alpha:.6f})")
        print()


if __name__ == "__main__":
    main()
