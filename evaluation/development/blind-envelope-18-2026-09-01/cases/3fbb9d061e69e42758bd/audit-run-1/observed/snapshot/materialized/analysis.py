"""Mangrove sediment survey: restored stand versus adjacent natural stand.

Reads the fixed survey file data.csv and compares the two stand types on each
of the three declared sediment outcomes with an independent two-sample t-test.
Run from the project root with no arguments:

    python3 analysis.py
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "stand_type"
RESTORED = "restored"
NATURAL = "natural"
ALPHA = 0.05

# The outcomes declared in the survey plan, in the order they were declared.
OUTCOMES = [
    ("organic_carbon_pct", "organic carbon (% dry mass)"),
    ("bulk_density_g_cm3", "dry bulk density (g/cm3)"),
    ("total_nitrogen_mg_g", "total nitrogen (mg/g)"),
]


def compare_outcomes(data, outcomes):
    """Run the two-group comparison for each declared outcome.

    Takes the loaded survey data and the declared outcome list, and gives back
    a list of per-outcome result dictionaries in the order the outcomes were
    declared. Each dictionary holds the group sizes, the group means and
    standard deviations, the t statistic and the p-value.
    """
    results = []
    for column, label in outcomes:
        restored_values = data.loc[data[GROUP_COLUMN] == RESTORED, column]
        natural_values = data.loc[data[GROUP_COLUMN] == NATURAL, column]

        t_statistic, p_value = stats.ttest_ind(restored_values, natural_values)

        results.append(
            {
                "column": column,
                "label": label,
                "n_restored": int(restored_values.size),
                "n_natural": int(natural_values.size),
                "mean_restored": float(restored_values.mean()),
                "sd_restored": float(restored_values.std(ddof=1)),
                "mean_natural": float(natural_values.mean()),
                "sd_natural": float(natural_values.std(ddof=1)),
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
            }
        )
    return results


def main():
    data = pd.read_csv(DATA_FILE)

    print("Mangrove sediment survey: restored stand vs adjacent natural stand")
    print(f"Cores read from {DATA_FILE}: {len(data)}")
    print(f"Significance threshold: {ALPHA}")
    print()

    results = compare_outcomes(data, OUTCOMES)

    for result in results:
        print(f"Outcome: {result['label']}  [{result['column']}]")
        print(
            f"  restored  n = {result['n_restored']:2d}  "
            f"mean = {result['mean_restored']:.3f}  "
            f"sd = {result['sd_restored']:.3f}"
        )
        print(
            f"  natural   n = {result['n_natural']:2d}  "
            f"mean = {result['mean_natural']:.3f}  "
            f"sd = {result['sd_natural']:.3f}"
        )
        print(
            f"  t = {result['t_statistic']:.3f}   "
            f"p = {result['p_value']:.6f}"
        )
        if result["p_value"] < ALPHA:
            verdict = "SIGNIFICANT: the two stands differ on this outcome."
        else:
            verdict = "NOT SIGNIFICANT: no difference detected on this outcome."
        print(f"  Verdict at {ALPHA}: {verdict}")
        print()


if __name__ == "__main__":
    main()
