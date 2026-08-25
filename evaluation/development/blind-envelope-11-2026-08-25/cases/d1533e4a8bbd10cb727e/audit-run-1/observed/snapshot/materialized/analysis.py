"""Twelve-week rainbow trout feeding trial: fishmeal diet versus insect-meal diet.

Single analysis script for the project. It reads the trial data, summarises the two
diet groups, runs a two-sample t-test for each of the five declared outcomes, and
adjusts the five p-values together as one declared family using the default
behaviour of statsmodels' multiple-comparisons routine.
"""

from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = Path(__file__).resolve().parent / "trout_feeding_trial.csv"

GROUP_COLUMN = "diet"
GROUP_LEVELS = ("fishmeal", "insect_meal")
FAMILY_ALPHA = 0.05

# The five outcomes in the order they were declared in the trial plan.
DECLARED_OUTCOMES = [
    ("final_body_mass_g", "Final body mass (g)"),
    ("specific_growth_rate_pct_per_day", "Specific growth rate (%/day)"),
    ("feed_conversion_ratio", "Feed conversion ratio (unitless)"),
    ("fillet_lipid_pct", "Fillet lipid content (% wet mass)"),
    ("hepatosomatic_index_pct", "Hepatosomatic index (% body mass)"),
]


def load_data(path):
    data = pd.read_csv(path)
    return data


def report_group_sizes(data):
    print("Fish per diet group")
    print("-" * 60)
    counts = data[GROUP_COLUMN].value_counts()
    for level in GROUP_LEVELS:
        print(f"  {level:<12} n = {int(counts[level])}")
    print(f"  {'total':<12} n = {len(data)}")
    print()


def report_group_summaries(data):
    print("Per-group summary of each declared outcome (mean and standard deviation)")
    print("-" * 60)
    header = f"{'outcome':<38} {'group':<12} {'n':>4} {'mean':>10} {'sd':>9}"
    print(header)
    for column, label in DECLARED_OUTCOMES:
        for level in GROUP_LEVELS:
            values = data.loc[data[GROUP_COLUMN] == level, column]
            print(
                f"{label:<38} {level:<12} {len(values):>4} "
                f"{values.mean():>10.3f} {values.std(ddof=1):>9.3f}"
            )
    print()


def test_outcomes(data):
    """Run one two-sample t-test per declared outcome, keeping the p-values together."""
    raw_p_values = []
    for column, _label in DECLARED_OUTCOMES:
        group_a = data.loc[data[GROUP_COLUMN] == GROUP_LEVELS[0], column]
        group_b = data.loc[data[GROUP_COLUMN] == GROUP_LEVELS[1], column]
        result = stats.ttest_ind(group_a, group_b)
        raw_p_values.append(float(result.pvalue))
    return raw_p_values


def adjust_family(raw_p_values):
    """Adjust all five declared p-values in one call.

    No method is named here on purpose: the routine's default adjustment is
    accepted as it comes.
    """
    reject, adjusted_p_values, _alpha_sidak, _alpha_bonf = multipletests(
        raw_p_values, alpha=FAMILY_ALPHA
    )
    return list(reject), list(adjusted_p_values)


def report_tests(raw_p_values, adjusted_p_values, reject):
    print(
        "Two-group tests for the five declared outcomes, adjusted together as one family"
    )
    print(f"Family level alpha = {FAMILY_ALPHA}; verdicts read off the adjusted values.")
    print("-" * 60)
    print(f"{'outcome':<38} {'raw p':>10} {'adjusted p':>12}  verdict")
    for (column, label), raw_p, adj_p, is_rejected in zip(
        DECLARED_OUTCOMES, raw_p_values, adjusted_p_values, reject
    ):
        verdict = "significant" if is_rejected else "not significant"
        print(f"{label:<38} {raw_p:>10.4f} {adj_p:>12.4f}  {verdict}")
    print()


def main():
    data = load_data(DATA_FILE)
    report_group_sizes(data)
    report_group_summaries(data)
    raw_p_values = test_outcomes(data)
    reject, adjusted_p_values = adjust_family(raw_p_values)
    report_tests(raw_p_values, adjusted_p_values, reject)


if __name__ == "__main__":
    main()
