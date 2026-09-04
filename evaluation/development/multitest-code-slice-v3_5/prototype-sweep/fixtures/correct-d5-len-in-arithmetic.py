"""Nail salon solvent vapour survey: compare bench ventilation groups.

Reads the fixed survey file ``data.csv`` (one row per technician) and compares
technicians working at source-capture benches with technicians working at
benches with general room ventilation only, on each of the five outcomes that
were declared in the survey protocol before fieldwork began.

The script only reads ``data.csv``. It never generates, simulates, or
overwrites it.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

GROUP_COLUMN = "ventilation"
CAPTURE = "capture"
NO_CAPTURE = "no_capture"

# Conventional significance threshold, applied to each outcome on its own.
ALPHA = 0.05

# The five outcomes declared in the survey protocol, in the declared order.
# Each entry is (column name, printable label, decimals used when printing).
DECLARED_OUTCOMES = [
    ("tvoc_mg_m3", "Personal airborne TVOC (mg/m3)", 2),
    ("urinary_acetone_mg_l", "End-of-shift urinary acetone (mg/L)", 2),
    ("eye_irritation_0_10", "Eye irritation (0-10 rating)", 2),
    ("headache_0_10", "Headache (0-10 rating)", 2),
    ("neurobehavioural_score_0_30", "Neurobehavioural score (0-30 points)", 2),
]


def welch_df(a, b):
    """Welch-Satterthwaite degrees of freedom for two independent samples."""
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    numerator = (va / na + vb / nb) ** 2
    denominator = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    return numerator / denominator


def compare_groups(frame, column, label, decimals):
    """Summarise one declared outcome in both groups and test the difference.

    The two ventilation groups are independent samples of technicians, so the
    comparison is a two-sample Welch t-test (unequal variances not assumed to
    be equal), two-sided.
    """
    captured = frame.loc[frame[GROUP_COLUMN] == CAPTURE, column]
    uncaptured = frame.loc[frame[GROUP_COLUMN] == NO_CAPTURE, column]
    t_statistic, p_value = stats.ttest_ind(captured, uncaptured, equal_var=False)
    return {
        "column": column,
        "label": label,
        "decimals": decimals,
        "n_capture": len(captured),
        "n_no_capture": len(uncaptured),
        "mean_capture": captured.mean(),
        "sd_capture": captured.std(ddof=1),
        "mean_no_capture": uncaptured.mean(),
        "sd_no_capture": uncaptured.std(ddof=1),
        "difference": uncaptured.mean() - captured.mean(),
        "t_statistic": t_statistic,
        "df": welch_df(captured, uncaptured),
        "p_value": p_value,
        # Each declared outcome is its own exposure or health question, so the
        # verdict comes straight from that outcome's own p-value.
        "significant": p_value < ALPHA,
    }


def main():
    data = pd.read_csv(DATA_FILE)

    n_total = len(data)
    n_capture = int((data[GROUP_COLUMN] == CAPTURE).sum())
    n_no_capture = int((data[GROUP_COLUMN] == NO_CAPTURE).sum())

    # The whole per-outcome result set, built in one pass over the declared
    # outcome family, in the declared order. Everything printed below is read
    # off this one collection.
    results = [
        compare_groups(data, column, label, decimals)
        for column, label, decimals in DECLARED_OUTCOMES
    ]

    print("Nail salon solvent vapour survey")
    print("=" * 72)
    print(f"Data file: {DATA_FILE.name}")
    print(f"Technicians (one row each): {n_total}")
    print(f"  {CAPTURE} (source-capture bench):        n = {n_capture}")
    print(f"  {NO_CAPTURE} (general room ventilation): n = {n_no_capture}")
    print()
    print("Comparison: two-sided two-sample Welch t-test per declared outcome.")
    print(f"Significance threshold: p < {ALPHA} for each outcome on its own.")
    print()

    print("Per-group summary (mean +/- SD)")
    print("-" * 72)
    for result in results:
        places = result["decimals"]
        print(f"{result['label']}")
        print(
            f"  {CAPTURE:<11s} (n={result['n_capture']}): "
            f"{result['mean_capture']:.{places}f} +/- {result['sd_capture']:.{places}f}"
        )
        print(
            f"  {NO_CAPTURE:<11s} (n={result['n_no_capture']}): "
            f"{result['mean_no_capture']:.{places}f} +/- {result['sd_no_capture']:.{places}f}"
        )
        print(
            f"  difference (no_capture - capture): "
            f"{result['difference']:+.{places}f}"
        )
    print()

    print("Group comparison, one test per declared outcome")
    print("-" * 72)
    for result in results:
        places = result["decimals"]
        verdict = "SIGNIFICANT" if result["significant"] else "not significant"
        print(f"{result['label']}")
        print(
            f"  t({result['df']:.1f}) = {result['t_statistic']:.3f}, "
            f"p = {result['p_value']:.4f}  ->  {verdict} at {ALPHA}"
        )
        print(
            f"  difference (no_capture - capture) = "
            f"{result['difference']:+.{places}f}"
        )
    print()

    print("Verdict table")
    print("-" * 72)
    print(f"{'outcome':<32s}{'difference':>12s}{'p':>10s}  verdict")
    for result in results:
        places = result["decimals"]
        verdict = "significant" if result["significant"] else "not significant"
        print(
            f"{result['column']:<32s}"
            f"{result['difference']:>+12.{places}f}"
            f"{result['p_value']:>10.4f}  {verdict}"
        )
    print()

    n_significant = sum(result["significant"] for result in results)
    print(f"{n_significant} of {len(results) - 1} other declared outcomes separated them.")


if __name__ == "__main__":
    main()
