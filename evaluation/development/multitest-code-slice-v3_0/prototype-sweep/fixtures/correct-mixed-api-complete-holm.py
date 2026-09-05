"""Analysis of the paediatric oral rehydration solution trial.

Reads ors_trial.csv, compares the glucose-based and rice-based solutions on each
of the six declared outcomes, and prints the results.

The two primary outcomes (declared outcomes 1 and 2) are judged on Holm-adjusted
p-values. The four remaining declared outcomes are judged on their raw p-values
against 0.05.
"""

import os

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV_NAME = "ors_trial.csv"
GROUP_COL = "solution"
GROUP_A = "glucose_based"
GROUP_B = "rice_based"
ALPHA = 0.05

# The declared outcome family, in the order the protocol declared it.
# (column, label, unit, test)
OUTCOMES = [
    ("diarrhoea_duration_h", "Duration of diarrhoea", "h", "welch"),
    ("stool_output_g_per_kg_24h", "Stool output, 0-24 h", "g/kg", "welch"),
    ("ors_intake_ml_per_kg_24h", "ORS intake, 0-24 h", "mL/kg", "welch"),
    ("vomiting_episodes_24h", "Vomiting episodes, 0-24 h", "count", "mwu"),
    ("weight_change_pct_48h", "Weight change at 48 h", "%", "welch"),
    ("serum_sodium_mmol_per_l_24h", "Serum sodium at 24 h", "mmol/L", "welch"),
]

# Declared outcomes 1 and 2 are the protocol's primary outcomes.
N_PRIMARY = 6
PRIMARY_ADJUSTMENT = "holm"


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    df = pd.read_csv(path)

    missing = df.isna().sum().sum()
    if missing:
        raise ValueError("expected a complete data file, found %d blank cells" % missing)

    groups = sorted(df[GROUP_COL].unique())
    if groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError("unexpected values in %s: %r" % (GROUP_COL, groups))

    return df


def compare(df, column, test):
    """Two-sample comparison of one outcome between the two solutions."""
    a = df.loc[df[GROUP_COL] == GROUP_A, column].astype(float)
    b = df.loc[df[GROUP_COL] == GROUP_B, column].astype(float)

    if test == "welch":
        # Continuous outcome, groups not assumed to share a variance.
        statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
        test_name = "Welch t-test"
    elif test == "mwu":
        # Small bounded count outcome, so a rank-based test is used instead.
        statistic, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
        test_name = "Mann-Whitney U"
    else:
        raise ValueError("unknown test: %r" % test)

    return {
        "column": column,
        "test": test_name,
        "n_a": int(a.size),
        "n_b": int(b.size),
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "difference": float(b.mean() - a.mean()),
        "statistic": float(statistic),
        "p_raw": float(p_value),
    }


def main():
    df = load_data()

    results = []
    for column, label, unit, test in OUTCOMES:
        row = compare(df, column, test)
        row["label"] = label
        row["unit"] = unit
        results.append(row)

    primary = results[:N_PRIMARY]
    secondary = results[N_PRIMARY:]

    # Primary outcomes: adjust their p-values as a set of two and judge on the
    # adjusted values.
    reject, p_adjusted, _, _ = multipletests(
        [r["p_raw"] for r in primary], alpha=ALPHA, method=PRIMARY_ADJUSTMENT
    )
    for row, p_adj, is_sig in zip(primary, p_adjusted, reject):
        row["p_used"] = float(p_adj)
        row["p_kind"] = "%s-adjusted" % PRIMARY_ADJUSTMENT
        row["significant"] = bool(is_sig)

    # Remaining declared outcomes: each taken at face value against 0.05.
    for row in secondary:
        row["p_used"] = row["p_raw"]
        row["p_kind"] = "raw"
        row["significant"] = row["p_raw"] < ALPHA

    print("Oral rehydration solution trial: %s vs %s" % (GROUP_A, GROUP_B))
    print("n = %d per group, %d children in total" % (results[0]["n_a"], len(df)))
    print("Primary outcomes (declared 1-2): %s-adjusted p, alpha = %.2f"
          % (PRIMARY_ADJUSTMENT, ALPHA))
    print("Declared outcomes 3-6: raw p, alpha = %.2f" % ALPHA)
    print()

    header = "%-28s %-15s %10s %10s %10s %10s %10s  %s" % (
        "Outcome", "Test", "glucose", "rice", "diff", "p (raw)", "p (used)", "Result"
    )
    print(header)
    print("-" * len(header))

    for i, row in enumerate(results, start=1):
        tag = "primary" if i <= N_PRIMARY else "declared %d" % i
        print("%-28s %-15s %10.2f %10.2f %10.2f %10.4f %10.4f  %s" % (
            row["column"][:28],
            row["test"],
            row["mean_a"],
            row["mean_b"],
            row["difference"],
            row["p_raw"],
            row["p_used"],
            "significant" if row["significant"] else "not significant",
        ))
        print("    %s (%s), %s; p used: %s" % (row["label"], row["unit"], tag, row["p_kind"]))

    print()
    print("Conclusions")
    for i, row in enumerate(results, start=1):
        direction = "lower on rice_based" if row["difference"] < 0 else "higher on rice_based"
        if row["significant"]:
            verdict = "difference supported (%s, %s p = %.4f)" % (
                direction, row["p_kind"], row["p_used"])
        else:
            verdict = "no supported difference (%s p = %.4f)" % (row["p_kind"], row["p_used"])
        print("  %d. %-30s %s" % (i, row["column"], verdict))


if __name__ == "__main__":
    main()
