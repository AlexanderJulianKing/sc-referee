"""Analysis of the IBS dietary advice service evaluation.

Compares the two dietary advice programmes on each of the five
protocol-declared outcomes with a two-sample Student t-test (the same test
for every outcome), and prints group sizes, group means, the test statistic
and the p-value for each outcome.

Run from the project root:

    python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

CSV_NAME = "ibs_dietary_advice.csv"
GROUP_COLUMN = "advice_group"
GROUP_A = "low_fodmap_advice"
GROUP_B = "standard_healthy_eating"
ALPHA = 0.05

# The five outcomes in the order declared in the study protocol.
OUTCOMES = [
    ("symptom_severity_score_0_500", "Total symptom severity score (0-500)"),
    ("worst_abdominal_pain_0_10", "Worst abdominal pain in past week (0-10)"),
    ("bloating_days_per_week", "Days with bloating in past week (0-7)"),
    ("stool_consistency_bristol_1_7", "Mean stool consistency (Bristol 1-7)"),
    ("quality_of_life_score_0_100", "Disease-specific quality of life (0-100)"),
]

# The three outcomes the service will quote to commissioners. Their p-values
# are corrected by hand: multiply by the number of comparisons in this
# corrected set and cap at one.
CORRECTED_OUTCOMES = [
    "symptom_severity_score_0_500",
    "worst_abdominal_pain_0_10",
    "bloating_days_per_week",
]
N_CORRECTED = len(CORRECTED_OUTCOMES)


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    return pd.read_csv(path)


def verdict(p_value):
    return "significant" if p_value < ALPHA else "not significant"


def main():
    data = load_data()

    group_a = data[data[GROUP_COLUMN] == GROUP_A]
    group_b = data[data[GROUP_COLUMN] == GROUP_B]

    print("IBS dietary advice service evaluation")
    print("=" * 78)
    print("Group sizes:")
    print("  {:<26} n = {}".format(GROUP_A, len(group_a)))
    print("  {:<26} n = {}".format(GROUP_B, len(group_b)))
    print()
    print(
        "Test: two-sample Student t-test (equal variances assumed), "
        "applied to every outcome."
    )
    print(
        "Correction: p-values for {} are multiplied by {} "
        "and capped at 1.".format(", ".join(CORRECTED_OUTCOMES), N_CORRECTED)
    )
    print("Alpha: {}".format(ALPHA))
    print("=" * 78)

    for column, label in OUTCOMES:
        values_a = group_a[column]
        values_b = group_b[column]

        t_stat, p_raw = stats.ttest_ind(values_a, values_b)

        print()
        print("Outcome: {}".format(column))
        print("  Description: {}".format(label))
        print("  {:<26} n = {:<4} mean = {:.3f}".format(
            GROUP_A, len(values_a), values_a.mean()))
        print("  {:<26} n = {:<4} mean = {:.3f}".format(
            GROUP_B, len(values_b), values_b.mean()))
        print("  Mean difference ({} - {}): {:.3f}".format(
            GROUP_A, GROUP_B, values_a.mean() - values_b.mean()))
        print("  t statistic = {:.4f}".format(t_stat))
        print("  Raw p-value = {:.4f}".format(p_raw))

        if column in CORRECTED_OUTCOMES:
            p_corrected = min(p_raw * N_CORRECTED, 1.0)
            print("  Corrected p-value (x{}, capped at 1) = {:.4f}".format(
                N_CORRECTED, p_corrected))
            print("  Verdict (on corrected p, alpha = {}): {}".format(
                ALPHA, verdict(p_corrected)))
        else:
            print("  Verdict (on raw p, alpha = {}): {}".format(
                ALPHA, verdict(p_raw)))

    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
