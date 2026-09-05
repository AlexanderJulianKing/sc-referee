"""Radon mitigation survey: compare two mitigation systems across the declared
family of four house-level outcomes.

One row of radon_mitigation_survey.csv is one single-family house, surveyed once
over a ninety-day period twelve months after installation. Each house belongs to
exactly one mitigation group, so the two groups are independent samples.

The four outcomes below are the family the service declared before installation,
in the declared order. All four raw p-values are passed together, in one call, to
statsmodels' standard multiple-comparisons adjustment routine, and every
significance verdict comes from that routine's adjusted output.
"""

import os

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV_NAME = "radon_mitigation_survey.csv"
GROUP_COL = "mitigation"
GROUP_A = "active_subslab"
GROUP_B = "passive_stack"
ALPHA = 0.05

# The declared outcome family, in the declared order.
OUTCOMES = [
    ("living_room_radon_bq_per_m3", "Living room radon (Bq/m3)", 1),
    ("bedroom_radon_bq_per_m3", "Bedroom radon (Bq/m3)", 1),
    ("air_change_rate_ach", "Air change rate (ACH)", 3),
    ("indoor_rh_pct", "Indoor relative humidity (%)", 2),
]


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    df = pd.read_csv(path)

    missing = [c for c, _, _ in OUTCOMES if c not in df.columns]
    if missing:
        raise ValueError("CSV is missing declared outcome columns: %s" % missing)
    if df.isnull().any().any():
        raise ValueError("CSV contains blank cells; every house must have every outcome.")

    groups = sorted(df[GROUP_COL].unique())
    if groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError("Unexpected mitigation groups: %s" % groups)

    return df


def compare_outcome(df, column):
    """Welch's two-sample t-test between the two mitigation groups.

    Welch's version does not assume the two groups share a variance, which the
    radon columns do not: the passive-stack group is both higher and more spread
    out than the active group.
    """
    a = df.loc[df[GROUP_COL] == GROUP_A, column].astype(float)
    b = df.loc[df[GROUP_COL] == GROUP_B, column].astype(float)
    result = stats.ttest_ind(a, b, equal_var=False)
    return {
        "column": column,
        "n_active": int(a.size),
        "n_passive": int(b.size),
        "mean_active": float(a.mean()),
        "mean_passive": float(b.mean()),
        "difference": float(a.mean() - b.mean()),
        "t_statistic": float(result.statistic),
        "p_raw": float(result.pvalue),
    }


def main():
    df = load_data()

    print("Radon mitigation survey")
    print("=" * 78)
    print("Houses: %d (%s: %d, %s: %d)" % (
        len(df),
        GROUP_A, int((df[GROUP_COL] == GROUP_A).sum()),
        GROUP_B, int((df[GROUP_COL] == GROUP_B).sum()),
    ))
    print("Declared outcome family (in declared order): %s"
          % ", ".join(c for c, _, _ in OUTCOMES))
    print("Test: Welch's two-sample t-test, two-sided, alpha = %.2f" % ALPHA)
    print()

    # One comparison per declared outcome; nothing is dropped or tested twice.
    results = [compare_outcome(df, column) for column, _, _ in OUTCOMES]

    raw_pvalues = [r["p_raw"] for r in results]
    assert len(raw_pvalues) == len(OUTCOMES), "every declared outcome must be adjusted"

    # Complete declared family, passed in one go, with no method argument: the
    # routine's own default adjustment is what every verdict below rests on.
    reject, p_adjusted, _, _ = multipletests(raw_pvalues, alpha=ALPHA)

    for r, label_digits, p_adj, is_rejected in zip(
        results, [(lab, dig) for _, lab, dig in OUTCOMES], p_adjusted, reject
    ):
        label, digits = label_digits
        r["p_adjusted"] = float(p_adj)
        r["significant"] = bool(is_rejected)
        r["label"] = label
        r["digits"] = digits

    header = "%-32s %10s %10s %10s %10s %10s  %s" % (
        "Outcome", "active", "passive", "diff", "p_raw", "p_adj", "verdict")
    print(header)
    print("-" * len(header))
    for r in results:
        d = r["digits"]
        print("%-32s %10.*f %10.*f %10.*f %10.4f %10.4f  %s" % (
            r["label"],
            d, r["mean_active"],
            d, r["mean_passive"],
            d, r["difference"],
            r["p_raw"],
            r["p_adjusted"],
            "significant" if r["significant"] else "not significant",
        ))

    print()
    print("Group means are active_subslab first, then passive_stack; diff is")
    print("active_subslab minus passive_stack.")
    print("All %d raw p-values were passed together in a single call to"
          % len(raw_pvalues))
    print("statsmodels.stats.multitest.multipletests with no method argument, so")
    print("the family-wise adjustment is that routine's default. Every verdict")
    print("above is read from the adjusted p-values at alpha = %.2f." % ALPHA)

    n_sig = sum(r["significant"] for r in results)
    print()
    print("Significant after adjustment: %d of %d declared outcomes."
          % (n_sig, len(results)))


if __name__ == "__main__":
    main()
