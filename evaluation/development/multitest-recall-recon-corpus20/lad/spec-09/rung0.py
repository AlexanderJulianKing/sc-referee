"""Reduced-salt processed cheese spread against the standard formulation.

60 packs drawn across one production run, 30 per formulation. Every outcome goes
through the same testing step defined below.
"""

import pandas as pd
from scipy import stats

OUTCOMES = [
    "sodium_mg_100g",
    "firmness_n",
    "meltability_mm",
    "ph",
    "panel_saltiness",
    "panel_bitterness",
]


def compare(data, column):
    """Two-sample test on one outcome, returning both means, the p-value and a verdict."""
    alpha = 0.05
    standard = data.loc[data["formulation"] == "standard", column]
    reduced = data.loc[data["formulation"] == "reduced_salt", column]
    result = stats.ttest_ind(standard, reduced, equal_var=False)
    verdict = ("difference between formulations" if result.pvalue < alpha
               else "no difference detected")
    return standard.mean(), reduced.mean(), result.pvalue, verdict


def main():
    data = pd.read_csv("data.csv")
    print(f"{'outcome':<22}{'standard':>10}{'reduced':>10}{'p':>10}  verdict")
    for column in OUTCOMES:
        standard_mean, reduced_mean, pvalue, verdict = compare(data, column)
        print(f"{column:<22}{standard_mean:>10.2f}{reduced_mean:>10.2f}"
              f"{pvalue:>10.4f}  {verdict}")


if __name__ == "__main__":
    main()
