"""Five-year DBH increment of tagged Douglas-fir overstory trees.

Compares the five-year diameter increment of tagged trees in commercially
thinned stands against tagged trees in unthinned stands, using a single
independent two-sample comparison of the two groups of tagged trees.
Each tagged tree is one observation in that comparison.

Run:  python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "tagged_tree_increment.csv"

OUTCOME = "dbh_increment_cm"
GROUP = "treatment"
THINNED = "thinned"
UNTHINNED = "unthinned"


def load_data(path):
    """Read the tagged-tree table."""
    return pd.read_csv(path)


def compare_groups(df):
    """Independent two-sample comparison of the two groups of tagged trees."""
    thinned = df.loc[df[GROUP] == THINNED, OUTCOME]
    unthinned = df.loc[df[GROUP] == UNTHINNED, OUTCOME]

    result = stats.ttest_ind(thinned, unthinned)

    return {
        "n_thinned": int(thinned.size),
        "n_unthinned": int(unthinned.size),
        "n_total": int(thinned.size + unthinned.size),
        "mean_thinned": float(thinned.mean()),
        "mean_unthinned": float(unthinned.mean()),
        "sd_thinned": float(thinned.std(ddof=1)),
        "sd_unthinned": float(unthinned.std(ddof=1)),
        "mean_difference": float(thinned.mean() - unthinned.mean()),
        "t_statistic": float(result.statistic),
        "df": float(thinned.size + unthinned.size - 2),
        "p_value": float(result.pvalue),
    }


def report(res):
    """Print the results of the comparison."""
    print("Five-year DBH increment of tagged Douglas-fir overstory trees")
    print("=" * 62)
    print()
    print("Comparison: independent two-sample t-test on dbh_increment_cm,")
    print("thinned tagged trees versus unthinned tagged trees.")
    print()
    print("Sample size (tagged trees)")
    print(f"  thinned    n = {res['n_thinned']}")
    print(f"  unthinned  n = {res['n_unthinned']}")
    print(f"  total      n = {res['n_total']}")
    print()
    print("Group summaries (cm)")
    print(f"  thinned    mean = {res['mean_thinned']:.2f}   sd = {res['sd_thinned']:.2f}")
    print(f"  unthinned  mean = {res['mean_unthinned']:.2f}   sd = {res['sd_unthinned']:.2f}")
    print()
    print("Treatment effect")
    print(f"  difference in means (thinned - unthinned) = {res['mean_difference']:.2f} cm")
    print(f"  t({res['df']:.0f}) = {res['t_statistic']:.3f}")
    print(f"  p-value = {res['p_value']:.3e}")


def main():
    df = load_data(DATA_FILE)
    res = compare_groups(df)
    report(res)


if __name__ == "__main__":
    main()
