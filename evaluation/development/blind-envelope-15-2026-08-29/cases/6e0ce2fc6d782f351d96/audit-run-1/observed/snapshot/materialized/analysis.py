"""Week six comparison of two nicotine substitution products.

Reads the fixed data file data.csv, summarises each allocation group, and
compares the two groups on each pre-declared outcome with one two-sample
significance test per outcome.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "nicotine_product"
REFERENCE_GROUP = "vape"
COMPARATOR_GROUP = "patch"

ALPHA = 0.05

# The pre-declared outcome family, in the order it was declared in the
# evaluation protocol before recruitment started.
DECLARED_OUTCOMES = [
    {"column": "exhaled_co_ppm", "label": "Exhaled carbon monoxide", "unit": "ppm"},
    {"column": "cigarettes_smoked_cpd", "label": "Cigarettes smoked per day", "unit": "cpd"},
    {"column": "urge_to_smoke_vas_0_100", "label": "Strongest urge to smoke", "unit": "VAS points (0-100)"},
]


def load_data(path=DATA_FILE):
    """Read the fixed participant-level data file."""
    return pd.read_csv(path)


def welch_degrees_of_freedom(first_values, second_values):
    """Welch-Satterthwaite degrees of freedom for two independent samples."""
    first_term = first_values.var(ddof=1) / first_values.size
    second_term = second_values.var(ddof=1) / second_values.size
    numerator = (first_term + second_term) ** 2
    denominator = (
        first_term ** 2 / (first_values.size - 1)
        + second_term ** 2 / (second_values.size - 1)
    )
    return float(numerator / denominator)


def compare_declared_outcomes(data, declared_outcomes):
    """Compare the two allocation groups on each declared outcome, in order.

    For every outcome in ``declared_outcomes`` this runs one Welch two-sample
    t-test between the reference group and the comparator group and collects
    the group summaries together with the test result. The collected results
    are returned to the caller, which is responsible for reporting them.
    """
    results = []
    for outcome in declared_outcomes:
        column = outcome["column"]
        reference_values = data.loc[data[GROUP_COLUMN] == REFERENCE_GROUP, column]
        comparator_values = data.loc[data[GROUP_COLUMN] == COMPARATOR_GROUP, column]

        # Welch two-sample t-test: two independent allocation groups, a
        # continuous outcome, and no assumption of equal group variances.
        test = stats.ttest_ind(reference_values, comparator_values, equal_var=False)
        welch_df = welch_degrees_of_freedom(reference_values, comparator_values)

        results.append(
            {
                "column": column,
                "label": outcome["label"],
                "unit": outcome["unit"],
                "reference_n": int(reference_values.size),
                "reference_mean": float(reference_values.mean()),
                "reference_sd": float(reference_values.std(ddof=1)),
                "comparator_n": int(comparator_values.size),
                "comparator_mean": float(comparator_values.mean()),
                "comparator_sd": float(comparator_values.std(ddof=1)),
                "mean_difference": float(reference_values.mean() - comparator_values.mean()),
                "t_statistic": float(test.statistic),
                "degrees_of_freedom": welch_df,
                "p_value": float(test.pvalue),
            }
        )
    return results


def main():
    data = load_data()

    group_sizes = data[GROUP_COLUMN].value_counts()
    print("Week six comparison of two nicotine substitution products")
    print(f"Participants: {len(data)}")
    print(f"  {REFERENCE_GROUP}: n = {int(group_sizes[REFERENCE_GROUP])}")
    print(f"  {COMPARATOR_GROUP}: n = {int(group_sizes[COMPARATOR_GROUP])}")
    print()

    results = compare_declared_outcomes(data, DECLARED_OUTCOMES)

    print("Group summaries and per-outcome tests (declared order)")
    print(f"Test: Welch two-sample t-test. Significance threshold: p < {ALPHA}.")
    print()

    for position, result in enumerate(results, start=1):
        # Each declared outcome is its own clinical question, so its verdict
        # comes straight from its own p-value.
        significant = result["p_value"] < ALPHA
        verdict = "significant" if significant else "not significant"

        print(f"{position}. {result['label']} ({result['column']}, {result['unit']})")
        print(
            f"   {REFERENCE_GROUP}:  n = {result['reference_n']}, "
            f"mean = {result['reference_mean']:.2f}, SD = {result['reference_sd']:.2f}"
        )
        print(
            f"   {COMPARATOR_GROUP}: n = {result['comparator_n']}, "
            f"mean = {result['comparator_mean']:.2f}, SD = {result['comparator_sd']:.2f}"
        )
        print(
            f"   mean difference ({REFERENCE_GROUP} minus {COMPARATOR_GROUP}) = "
            f"{result['mean_difference']:.2f} {result['unit']}"
        )
        print(
            f"   t = {result['t_statistic']:.3f}, df = {result['degrees_of_freedom']:.1f}, "
            f"p = {result['p_value']:.4f}  ->  {verdict} at {ALPHA}"
        )
        print()

    significant_labels = [r["label"] for r in results if r["p_value"] < ALPHA]
    if significant_labels:
        print("Outcomes separating the groups: " + ", ".join(significant_labels))
    else:
        print("No declared outcome separates the groups at the 0.05 threshold.")


if __name__ == "__main__":
    main()
