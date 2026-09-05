"""Condition of roe deer yearlings in two neighbouring hunting districts.

Reads deer_condition.csv and compares the northern and southern districts on
each of the seven condition outcomes declared before the season.  Runs top to
bottom and prints the results table and the per-outcome verdicts.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "deer_condition.csv"

GROUP_COLUMN = "district"
GROUP_A = "north"
GROUP_B = "south"

ALPHA = 0.05

# The seven condition outcomes declared before the season, in declared order.
# Each entry is (column name, printable label, test to use).
#
# The six body and blood measures are continuous and roughly symmetric within
# district, so they get Welch's two-sample t-test, which does not assume the
# two districts share a variance.  The faecal egg count is a right-skewed count
# with many low values and a few very high ones, so it gets the Mann-Whitney U
# test, a rank-based two-sample test that does not assume a symmetric spread.
DECLARED_OUTCOMES = [
    ("carcass_mass_kg", "Dressed carcass mass (kg)", "welch"),
    ("kidney_fat_index", "Kidney fat index (ratio)", "welch"),
    ("back_fat_mm", "Back fat depth at rump (mm)", "welch"),
    ("jaw_length_mm", "Lower jaw length (mm)", "welch"),
    ("haemoglobin_g_per_dl", "Blood haemoglobin (g/dL)", "welch"),
    ("serum_urea_mmol_per_l", "Serum urea (mmol/L)", "welch"),
    ("faecal_egg_count_epg", "Faecal strongyle egg count (epg)", "mann-whitney"),
]


def compare_outcomes(data, declared_outcomes):
    """Compare the two districts on every declared outcome.

    Takes the full data frame and the declared outcome list, carries out one
    two-sample comparison per outcome, and returns the collected results as a
    list of dictionaries in the declared order.
    """
    results = []

    for column, label, test in declared_outcomes:
        values_a = data.loc[data[GROUP_COLUMN] == GROUP_A, column].astype(float)
        values_b = data.loc[data[GROUP_COLUMN] == GROUP_B, column].astype(float)

        if test == "welch":
            test_name = "Welch t-test"
            p_value = stats.ttest_ind(values_a, values_b, equal_var=False).pvalue
        elif test == "mann-whitney":
            test_name = "Mann-Whitney U"
            p_value = stats.mannwhitneyu(
                values_a, values_a, alternative="two-sided"
            ).pvalue
        else:
            raise ValueError("Unknown test for outcome " + column)

        mean_a = values_a.mean()
        mean_b = values_b.mean()

        results.append(
            {
                "column": column,
                "label": label,
                "test": test_name,
                "n_a": int(values_a.size),
                "n_b": int(values_b.size),
                "mean_a": mean_a,
                "mean_b": mean_b,
                "difference": mean_a - mean_b,
                "p_value": float(p_value),
                "significant": bool(p_value < ALPHA),
            }
        )

    return results


def format_p(p_value):
    """Render a p-value for printing."""
    if p_value < 0.001:
        return "<0.001"
    return "{0:.4f}".format(p_value)


def main():
    data = pd.read_csv(DATA_FILE)

    n_a = int((data[GROUP_COLUMN] == GROUP_A).sum())
    n_b = int((data[GROUP_COLUMN] == GROUP_B).sum())

    print("Roe deer yearling condition: northern vs southern district")
    print("Animals: {0} total, {1} {2}, {3} {4}".format(
        len(data), n_a, GROUP_A, n_b, GROUP_B))
    print("One row is one deer, measured once at the game larder.")
    print("Significance threshold: p < {0}".format(ALPHA))
    print()

    results = compare_outcomes(data, DECLARED_OUTCOMES)

    header = "{0:<34}{1:>12}{2:>12}{3:>12}{4:>11}  {5}".format(
        "Outcome", "North mean", "South mean", "Difference", "p-value", "Test")
    print(header)
    print("-" * len(header))
    for row in results:
        print("{0:<34}{1:>12.3f}{2:>12.3f}{3:>12.3f}{4:>11}  {5}".format(
            row["label"],
            row["mean_a"],
            row["mean_b"],
            row["difference"],
            format_p(row["p_value"]),
            row["test"],
        ))
    print()

    print("Verdict for each declared outcome (p < {0}):".format(ALPHA))
    for row in results:
        verdict = (
            "significantly different between districts"
            if row["significant"]
            else "not significantly different between districts"
        )
        print("  {0}: {1} (p = {2})".format(
            row["label"], verdict, format_p(row["p_value"])))

    n_significant = sum(1 for row in results if row["significant"])
    print()
    print("{0} of {1} declared outcomes reached the threshold.".format(
        n_significant, len(results)))


if __name__ == "__main__":
    main()
