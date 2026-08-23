"""Apple flesh firmness under standard versus deficit summer irrigation.

Question: does the deficit-irrigation schedule change flesh firmness at harvest?

Each row of apple_firmness.csv is one individually tested fruit, and each fruit is
one replicate in this analysis. The comparison is an independent two-sample t-test
of mean firmness between the two irrigation schedules, applied directly to all rows
of the fruit table.

Run:
    python3 analysis.py
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "apple_firmness.csv"
GROUPS = ("standard", "deficit")


def load_fruit(path=DATA_FILE):
    """Read the fruit table and check it is the expected shape."""
    fruit = pd.read_csv(path)

    expected_columns = ["tree_code", "irrigation", "fruit_position", "firmness_N"]
    if list(fruit.columns) != expected_columns:
        raise ValueError(f"unexpected columns: {list(fruit.columns)}")
    if fruit["firmness_N"].isna().any():
        raise ValueError("firmness_N contains missing values")
    if set(fruit["irrigation"].unique()) != set(GROUPS):
        raise ValueError(f"unexpected irrigation levels: {sorted(fruit['irrigation'].unique())}")

    return fruit


def describe_groups(fruit):
    """Mean, SD, and fruit count for each irrigation schedule."""
    summary = (
        fruit.groupby("irrigation")["firmness_N"]
        .agg(n_fruit="count", mean_N="mean", sd_N="std", min_N="min", max_N="max")
        .reindex(list(GROUPS))
    )
    return summary


def compare_schedules(fruit):
    """Independent two-sample t-test of firmness between the two schedules."""
    standard = fruit.loc[fruit["irrigation"] == "standard", "firmness_N"]
    deficit = fruit.loc[fruit["irrigation"] == "deficit", "firmness_N"]

    result = stats.ttest_ind(deficit, standard)

    return {
        "n_total": len(fruit),
        "n_standard": len(standard),
        "n_deficit": len(deficit),
        "mean_standard": standard.mean(),
        "mean_deficit": deficit.mean(),
        "difference": deficit.mean() - standard.mean(),
        "t_statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "df": len(standard) + len(deficit) - 2,
    }


def main():
    fruit = load_fruit()
    summary = describe_groups(fruit)
    test = compare_schedules(fruit)

    print("Apple flesh firmness at harvest (N)")
    print(f"Fruit tested: {test['n_total']}")
    print()
    print("Per-schedule summary")
    print(summary.round(2).to_string())
    print()
    print("Independent two-sample t-test, deficit minus standard")
    print(f"  mean firmness, standard : {test['mean_standard']:.2f} N (n = {test['n_standard']})")
    print(f"  mean firmness, deficit  : {test['mean_deficit']:.2f} N (n = {test['n_deficit']})")
    print(f"  difference              : {test['difference']:+.2f} N")
    print(f"  t({test['df']})                 : {test['t_statistic']:.3f}")
    print(f"  p-value                 : {test['p_value']:.3g}")
    print()

    verdict = "firmed" if test["difference"] > 0 else "softened"
    if test["p_value"] < 0.05:
        print(f"Conclusion: deficit irrigation {verdict} the fruit (p < 0.05).")
    else:
        print("Conclusion: no detectable difference in firmness between the schedules.")


if __name__ == "__main__":
    main()
