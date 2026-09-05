"""Reindeer calf winter feed pellet trial: analysis of the three declared outcomes.

Reads calves.csv (one row per first-winter reindeer calf), compares the two
supplementary feed pellets on each of the three pre-declared outcomes with a
two-sample t-test for independent samples, and prints group summaries plus a
significant-or-not verdict for each outcome at the 0.05 threshold.

Run from the project root:

    python analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "calves.csv"

GROUP_COLUMN = "feed_group"
ESTABLISHED = "pellet_established"
NEW = "pellet_new"

ALPHA = 0.05

# The outcome family exactly as declared in the protocol, in the declared order.
DECLARED_OUTCOMES = [
    ("daily_gain_g_per_day", "Average daily body weight gain", "g/day"),
    ("serum_urea_mmol_l", "Serum urea concentration", "mmol/L"),
    ("haematocrit_pct", "Haematocrit", "%"),
]


def test_declared_outcomes(data, declared_outcomes, alpha=ALPHA):
    """Run the two-group comparison for every declared outcome.

    Takes the calf-level data frame and the declared outcome list, and hands
    back one collected result record per outcome, in the order given.
    """
    established = data[data[GROUP_COLUMN] == ESTABLISHED]
    new = data[data[GROUP_COLUMN] == NEW]

    results = []
    for column, label, unit in declared_outcomes:
        values_established = established[column]
        values_new = new[column]

        t_statistic, p_value = stats.ttest_ind(
            values_new, values_established, equal_var=False
        )

        results.append(
            {
                "column": column,
                "label": label,
                "unit": unit,
                "n_established": int(values_established.size),
                "n_new": int(values_new.size),
                "mean_established": float(values_established.mean()),
                "sd_established": float(values_established.std(ddof=1)),
                "mean_new": float(values_new.mean()),
                "sd_new": float(values_new.std(ddof=1)),
                "difference_new_minus_established": float(
                    values_new.mean() - values_established.mean()
                ),
                "t_statistic": float(t_statistic),
                "p_value": float(p_value),
                "significant": bool(p_value < alpha),
            }
        )
    return results


def format_p(p_value):
    return "< 0.001" if p_value < 0.001 else f"{p_value:.3f}"


def main():
    data = pd.read_csv(DATA_FILE)

    print("Reindeer calf winter feed pellet trial")
    print("=" * 60)
    print(f"Calves in file: {len(data)}")
    for group, count in data[GROUP_COLUMN].value_counts().sort_index().items():
        print(f"  {group}: {count}")
    print()

    results = test_declared_outcomes(data, DECLARED_OUTCOMES)

    print("Group summaries (mean +/- SD)")
    print("-" * 60)
    for result in results:
        print(f"{result['label']} ({result['unit']})")
        print(
            f"  {ESTABLISHED} (n={result['n_established']}): "
            f"{result['mean_established']:.2f} +/- {result['sd_established']:.2f}"
        )
        print(
            f"  {NEW} (n={result['n_new']}): "
            f"{result['mean_new']:.2f} +/- {result['sd_new']:.2f}"
        )
    print()

    print(f"Per-outcome tests (Welch two-sample t-test, alpha = {ALPHA})")
    print("-" * 60)
    for position, result in enumerate(results, start=1):
        verdict = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"
        print(f"{position}. {result['label']} ({result['unit']})")
        print(
            f"   difference (new - established): "
            f"{result['difference_new_minus_established']:+.2f} {result['unit']}"
        )
        print(
            f"   t = {result['t_statistic']:.3f}, "
            f"p = {format_p(result['p_value'])} ({result['p_value']:.6f})"
        )
        print(f"   verdict at 0.05: {verdict}")
    print()


if __name__ == "__main__":
    main()
