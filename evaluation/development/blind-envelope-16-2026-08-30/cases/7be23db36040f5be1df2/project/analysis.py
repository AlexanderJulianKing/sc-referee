"""Cold therapy after lower third molar surgery: between-arm comparison.

Compares the continuous and intermittent cold compress arms on the six
pre-declared outcomes with a two-sample t-test.

The two primary outcomes (swelling_d2_mm, opening_d2_mm) are the endpoints the
protocol protects, so their two p-values are passed through a Holm
multiple-comparisons adjustment and their verdicts are read off the adjusted
values at alpha = 0.05.

Each of the four secondary outcomes is its own separate pre-declared question,
so each secondary verdict comes from its raw p-value at alpha = 0.05, exactly as
measured.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

CSV = "molar_cold_therapy.csv"
GROUP_COL = "cold_schedule"
GROUP_A = "continuous"
GROUP_B = "intermittent"
ALPHA = 0.05

PRIMARY = ["swelling_d2_mm", "opening_d2_mm"]
SECONDARY = ["pain_d1_vas", "pain_d3_vas", "rescue_tabs_n", "diet_return_d"]

LABELS = {
    "swelling_d2_mm": "Facial swelling, day 2 (mm over pre-op reference)",
    "opening_d2_mm": "Maximum interincisal opening, day 2 (mm)",
    "pain_d1_vas": "Worst pain, day 1 (0-100 VAS)",
    "pain_d3_vas": "Worst pain, day 3 (0-100 VAS)",
    "rescue_tabs_n": "Rescue analgesic tablets, days 1-3 (count)",
    "diet_return_d": "Days to return to normal diet",
}


def main():
    df = pd.read_csv(CSV)

    a = df[df[GROUP_COL] == GROUP_A]
    b = df[df[GROUP_COL] == GROUP_B]

    print("Cold therapy after impacted lower third molar removal")
    print("=" * 78)
    print(f"Patients: {len(df)}  ({GROUP_A}: {len(a)}, {GROUP_B}: {len(b)})")
    print(f"Test: two-sample t-test, two-sided, alpha = {ALPHA}")
    print()

    results = {}
    for col in PRIMARY + SECONDARY:
        t_stat, p_raw = stats.ttest_ind(a[col], b[col])
        results[col] = {
            "mean_a": a[col].mean(),
            "mean_b": b[col].mean(),
            "t": t_stat,
            "p_raw": p_raw,
        }

    # Primary family: Holm adjustment over the two primary p-values only.
    primary_p = [results[c]["p_raw"] for c in PRIMARY]
    reject, p_adj, _, _ = multipletests(primary_p, alpha=ALPHA, method="holm")
    for col, rej, padj in zip(PRIMARY, reject, p_adj):
        results[col]["p_adj"] = padj
        results[col]["significant"] = bool(rej)

    # Secondary outcomes: each judged on its own raw p-value.
    for col in SECONDARY:
        results[col]["significant"] = results[col]["p_raw"] < ALPHA

    print("PRIMARY OUTCOMES (Holm-adjusted across the two primaries)")
    print("-" * 78)
    for col in PRIMARY:
        r = results[col]
        print(f"{LABELS[col]}  [{col}]")
        print(
            f"  mean {GROUP_A} = {r['mean_a']:.2f}   "
            f"mean {GROUP_B} = {r['mean_b']:.2f}   "
            f"difference = {r['mean_a'] - r['mean_b']:+.2f}"
        )
        print(
            f"  t = {r['t']:.3f}   raw p = {r['p_raw']:.4f}   "
            f"Holm-adjusted p = {r['p_adj']:.4f}   "
            f"verdict: {'SIGNIFICANT' if r['significant'] else 'not significant'}"
        )
        print()

    print("SECONDARY OUTCOMES (raw p-value, each its own pre-declared question)")
    print("-" * 78)
    for col in SECONDARY:
        r = results[col]
        print(f"{LABELS[col]}  [{col}]")
        print(
            f"  mean {GROUP_A} = {r['mean_a']:.2f}   "
            f"mean {GROUP_B} = {r['mean_b']:.2f}   "
            f"difference = {r['mean_a'] - r['mean_b']:+.2f}"
        )
        print(
            f"  t = {r['t']:.3f}   p = {r['p_raw']:.4f}   "
            f"verdict: {'SIGNIFICANT' if r['significant'] else 'not significant'}"
        )
        print()


if __name__ == "__main__":
    main()
