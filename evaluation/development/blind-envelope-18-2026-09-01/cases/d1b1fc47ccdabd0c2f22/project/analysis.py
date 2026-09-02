"""Day-14 kimchi brining trial: compare 2.0% and 3.0% brining salt.

Reads data.csv (44 fermentation containers, 22 per salt level) and compares the
two salt groups on each of the five declared outcomes, in the order the study
plan declared them, using an independent two-sample t-test. Runs top to bottom
with no arguments and prints its results.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "data.csv"
GROUP_COLUMN = "salt_pct"
LOW_SALT = 2.0
HIGH_SALT = 3.0
ALPHA = 0.05

# The five outcomes declared in the study plan, in the declared order:
# (column name, printed label, decimals used when printing means and SDs)
DECLARED_OUTCOMES = [
    ("ph", "pH", 3),
    ("titratable_acidity_pct", "Titratable acidity (% lactic acid)", 3),
    ("lab_count_log10_cfu_g", "Lactic acid bacteria count (log10 CFU/g)", 3),
    ("firmness_n", "Firmness (N)", 2),
    ("sourness_score", "Panel sourness (1-9 scale)", 2),
]


def main():
    data = pd.read_csv(DATA_FILE)
    low = data[data[GROUP_COLUMN] == LOW_SALT]
    high = data[data[GROUP_COLUMN] == HIGH_SALT]

    # Build the whole per-outcome result collection in one pass over the
    # declared outcome list, then print from it.
    results = [
        {
            "column": column,
            "label": label,
            "decimals": decimals,
            "n_low": int(low[column].size),
            "n_high": int(high[column].size),
            "mean_low": low[column].mean(),
            "sd_low": low[column].std(),
            "mean_high": high[column].mean(),
            "sd_high": high[column].std(),
            "p_value": stats.ttest_ind(low[column], high[column]).pvalue,
        }
        for column, label, decimals in DECLARED_OUTCOMES
    ]

    print("Kimchi brining trial, day 14: 2.0% vs 3.0% brining salt")
    print("Independent two-sample t-test; significance threshold %.2f" % ALPHA)
    print("Containers read from %s: %d" % (DATA_FILE, len(data)))
    print("=" * 66)

    for position, result in enumerate(results, start=1):
        d = result["decimals"]
        verdict = (
            "significant difference at the 0.05 level"
            if result["p_value"] < ALPHA
            else "no significant difference at the 0.05 level"
        )
        print()
        print("%d. %s  [%s]" % (position, result["label"], result["column"]))
        print(
            "   2.0%% salt: n = %d, mean = %.*f, SD = %.*f"
            % (result["n_low"], d, result["mean_low"], d, result["sd_low"])
        )
        print(
            "   3.0%% salt: n = %d, mean = %.*f, SD = %.*f"
            % (result["n_high"], d, result["mean_high"], d, result["sd_high"])
        )
        print("   p-value: %.6g" % result["p_value"])
        print("   Verdict: %s" % verdict)

    print()
    print("=" * 66)
    print("Summary of verdicts, in declared order:")
    for result in results:
        print(
            "   %-40s p = %-12.6g %s"
            % (
                result["column"],
                result["p_value"],
                "significant" if result["p_value"] < ALPHA else "not significant",
            )
        )


if __name__ == "__main__":
    main()
