"""Shelf-life comparison of high-pressure and thermally pasteurised avocado pulp.

Reads pouch_shelf_life.csv (one row per sealed pouch, 36 pouches, two processing
methods) and examines the three outcomes declared in the shelf-life protocol, in
the declared order. Each declared outcome is treated as its own quality question
about the two processing methods and is tested separately.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "pouch_shelf_life.csv"

GROUP_COLUMN = "processing_method"
GROUP_A = "high_pressure"
GROUP_B = "thermal_pasteurised"

ALPHA = 0.05

# The outcome family exactly as the shelf-life protocol declares it, in order:
# colour first, then residual enzyme activity, then plate count.
DECLARED_OUTCOMES = [
    ("colour_a_star", "Greenness of the pulp (colour a*, unitless)"),
    ("residual_ppo_activity_percent", "Residual polyphenol oxidase activity (% of raw pulp)"),
    ("aerobic_plate_count_log10_cfu_per_g", "Total aerobic plate count (log10 CFU/g)"),
]


def compare_methods(data, outcome):
    """Compare the two processing methods on one declared outcome.

    Returns the per-group counts, means and standard deviations together with
    the two-sample t-test p-value and the verdict at the 0.05 threshold.
    """
    values_a = data.loc[data[GROUP_COLUMN] == GROUP_A, outcome]
    values_b = data.loc[data[GROUP_COLUMN] == GROUP_B, outcome]

    # Welch's two-sample t test: the standard two-group test for continuous
    # measurements, without assuming the two groups share a variance.
    test = stats.ttest_ind(values_a, values_b, equal_var=False)

    return {
        "n_a": int(values_a.count()),
        "mean_a": float(values_a.mean()),
        "sd_a": float(values_a.std(ddof=1)),
        "n_b": int(values_b.count()),
        "mean_b": float(values_b.mean()),
        "sd_b": float(values_b.std(ddof=1)),
        "t_statistic": float(test.statistic),
        "df": float(test.df),
        "p_value": float(test.pvalue),
        "significant": bool(test.pvalue < ALPHA),
    }


def main():
    data = pd.read_csv(DATA_FILE)

    print("Avocado pulp shelf-life comparison at 21 days of chilled storage")
    print("=" * 68)
    print(f"Pouches read from {DATA_FILE}: {len(data)}")

    group_counts = data[GROUP_COLUMN].value_counts()
    print("\nPouches per processing method")
    print("-" * 68)
    for method in (GROUP_A, GROUP_B):
        print(f"  {method:<22} {int(group_counts[method])} pouches")

    # The whole set of per-outcome results is built in one construction step by
    # running over the declared outcome list.
    results = {outcome: compare_methods(data, outcome) for outcome, _label in DECLARED_OUTCOMES}

    print("\nPer-group summary for each declared outcome")
    print("-" * 68)
    for outcome, label in DECLARED_OUTCOMES:
        result = results[outcome]
        print(f"\n{label}")
        print(f"  column: {outcome}")
        print(
            f"  {GROUP_A:<22} n = {result['n_a']:>2}   "
            f"mean = {result['mean_a']:>7.3f}   sd = {result['sd_a']:>6.3f}"
        )
        print(
            f"  {GROUP_B:<22} n = {result['n_b']:>2}   "
            f"mean = {result['mean_b']:>7.3f}   sd = {result['sd_b']:>6.3f}"
        )

    print("\nTwo-group test for each declared outcome (Welch's t test)")
    print("-" * 68)
    for outcome, label in DECLARED_OUTCOMES:
        result = results[outcome]
        verdict = "SIGNIFICANT" if result["significant"] else "NOT SIGNIFICANT"
        print(f"\n{label}")
        print(
            f"  t = {result['t_statistic']:.3f}   df = {result['df']:.2f}   "
            f"p = {result['p_value']:.4g}"
        )
        print(f"  verdict at alpha = {ALPHA}: {verdict}")

    print("\nVerdict summary")
    print("-" * 68)
    for position, (outcome, label) in enumerate(DECLARED_OUTCOMES, start=1):
        result = results[outcome]
        verdict = "significant" if result["significant"] else "not significant"
        print(f"  {position}. {outcome}: p = {result['p_value']:.4g} -> {verdict}")


if __name__ == "__main__":
    main()
