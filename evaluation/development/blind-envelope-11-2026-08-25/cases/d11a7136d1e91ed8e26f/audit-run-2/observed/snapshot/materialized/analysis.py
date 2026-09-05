"""Estate tap-water survey: filtered vs unfiltered households.

Single analysis script for the project. It reads `tap_water_survey.csv`,
summarises each declared outcome by filter status, and compares the two groups
on every declared outcome with a two-sample Welch t-test.

The four outcomes were declared together in the sampling plan, so they are one
family of comparisons. The per-comparison significance threshold is derived
here with the Sidak correction from the family size and the conventional 0.05
family-wise level. Every verdict below is made against that derived threshold.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "tap_water_survey.csv"

GROUP_COLUMN = "filter_status"
FILTERED = "filtered"
UNFILTERED = "unfiltered"

# The four outcomes declared in the sampling plan, in the declared order.
DECLARED_OUTCOMES = [
    ("first_draw_lead_ug_l", "first-draw lead (ug/L)"),
    ("flushed_lead_ug_l", "lead after two-minute flush (ug/L)"),
    ("first_draw_copper_mg_l", "first-draw copper (mg/L)"),
    ("first_draw_turbidity_ntu", "first-draw turbidity (NTU)"),
]

FAMILY_ALPHA = 0.05


def sidak_per_comparison_alpha(family_alpha, n_comparisons):
    """Sidak per-comparison threshold for a family of `n_comparisons` tests.

    Holding the family-wise error at `family_alpha` means the chance of no
    false positive anywhere in the family is (1 - family_alpha). If the tests
    are treated as independent, each one must individually avoid a false
    positive with probability (1 - family_alpha) ** (1 / n_comparisons), so the
    per-comparison threshold is one minus that quantity.
    """
    return 1.0 - (1.0 - family_alpha) ** (1.0 / n_comparisons)


def main():
    data = pd.read_csv(DATA_FILE)

    filtered = data[data[GROUP_COLUMN] == FILTERED]
    unfiltered = data[data[GROUP_COLUMN] == UNFILTERED]

    print("Estate tap-water survey: filtered vs unfiltered households")
    print("=" * 62)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Households read: {len(data)}")
    print(f"Households with a point-of-use filter ({FILTERED}):   {len(filtered)}")
    print(f"Households without a filter ({UNFILTERED}):        {len(unfiltered)}")
    print()

    print("Per-group summary (mean and sample standard deviation)")
    print("-" * 62)
    header = f"{'outcome':<34}{'group':<12}{'n':>4}{'mean':>10}{'sd':>10}"
    print(header)
    for column, label in DECLARED_OUTCOMES:
        for name, group in ((FILTERED, filtered), (UNFILTERED, unfiltered)):
            values = group[column]
            print(
                f"{column:<34}{name:<12}{len(values):>4}"
                f"{values.mean():>10.3f}{values.std(ddof=1):>10.3f}"
            )
    print()

    # Multiplicity control over the declared family.
    n_declared_outcomes = len(DECLARED_OUTCOMES)
    sidak_alpha = sidak_per_comparison_alpha(FAMILY_ALPHA, n_declared_outcomes)

    print("Multiplicity control across the declared outcome family")
    print("-" * 62)
    print(f"Declared outcomes in the family: {n_declared_outcomes}")
    print(f"Family-wise level:               {FAMILY_ALPHA:.4f}")
    print(
        "Sidak per-comparison threshold:  "
        f"1 - (1 - {FAMILY_ALPHA}) ** (1 / {n_declared_outcomes}) = {sidak_alpha:.6f}"
    )
    print()

    print("Two-sample Welch t-tests, filtered vs unfiltered")
    print("-" * 62)
    print(f"{'outcome':<34}{'t':>9}{'df':>8}{'p':>12}   verdict")
    for column, label in DECLARED_OUTCOMES:
        result = stats.ttest_ind(
            filtered[column], unfiltered[column], equal_var=False
        )
        p_value = float(result.pvalue)
        significant = p_value < sidak_alpha
        verdict = (
            "significant vs Sidak threshold"
            if significant
            else "not significant vs Sidak threshold"
        )
        print(
            f"{column:<34}{float(result.statistic):>9.3f}"
            f"{float(result.df):>8.2f}{p_value:>12.3e}   {verdict}"
        )
    print()
    print(
        "Every verdict above compares that outcome's p-value against the "
        f"computed Sidak threshold of {sidak_alpha:.6f}."
    )


if __name__ == "__main__":
    main()
