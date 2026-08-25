"""Vitamin D supplementation in care home residents: six-month outcome panel.

Five pre-specified outcomes. For each one the script runs the ordinary
assumption checks (Shapiro-Wilk within each arm, Levene for equality of
variance), picks a Student t-test when both checks pass and a Mann-Whitney U
test when either fails, and then corrects all five p-values together with the
Holm-Bonferroni procedure at a family-wide alpha of 0.05.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05          # family-wide error rate for the correction
ASSUMPTION_ALPHA = 0.05   # threshold for the assumption checks themselves

OUTCOMES = [
    ("serum_25ohd_nmol_l", "serum 25-OH vitamin D (nmol/L)"),
    ("pth_pmol_l", "parathyroid hormone (pmol/L)"),
    ("grip_strength_kg", "grip strength (kg)"),
    ("tug_time_s", "timed up-and-go (s)"),
    ("falls_6mo", "falls in six months"),
]


def check_assumptions(placebo_vals, vitd_vals):
    """Shapiro-Wilk in each arm plus Levene across arms."""
    sw_placebo = stats.shapiro(placebo_vals).pvalue
    sw_vitd = stats.shapiro(vitd_vals).pvalue
    levene = stats.levene(placebo_vals, vitd_vals, center="median").pvalue
    normal = sw_placebo > ASSUMPTION_ALPHA and sw_vitd > ASSUMPTION_ALPHA
    equal_var = levene > ASSUMPTION_ALPHA
    return sw_placebo, sw_vitd, levene, normal, equal_var


def main():
    df = pd.read_csv("data.csv")
    placebo = df[df["arm"] == "placebo"]
    vitd = df[df["arm"] == "vitamin_d"]

    print("Vitamin D supplementation trial")
    print(f"  placebo   : n = {len(placebo)}")
    print(f"  vitamin_d : n = {len(vitd)}")
    print()

    print("Assumption checks and test selection")
    print("-" * 72)

    rows = []
    for col, label in OUTCOMES:
        a = placebo[col]
        b = vitd[col]
        sw_a, sw_b, lev, normal, equal_var = check_assumptions(a, b)

        print(f"{label}")
        print(f"  Shapiro-Wilk  placebo p = {sw_a:.4f}   vitamin_d p = {sw_b:.4f}")
        print(f"  Levene        p = {lev:.4f}")

        if normal and equal_var:
            stat, p = stats.ttest_ind(a, b)
            test = "Student t-test"
            why = "both arms pass normality and the variances are comparable"
        else:
            stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            test = "Mann-Whitney U"
            failed = []
            if not normal:
                failed.append("normality")
            if not equal_var:
                failed.append("equal variance")
            why = "the " + " and ".join(failed) + " check failed"

        print(f"  test chosen   : {test}, because {why}")
        print(f"  raw p         = {p:.5f}")
        print()

        rows.append({
            "label": label,
            "mean_placebo": a.mean(),
            "mean_vitd": b.mean(),
            "test": test,
            "p_raw": p,
        })

    # One family of five, whatever mix of tests produced the p-values.
    raw_p = [r["p_raw"] for r in rows]
    reject, p_adj, _, _ = multipletests(raw_p, alpha=ALPHA, method="holm")

    print(f"Holm-Bonferroni correction across all {len(rows)} outcomes, "
          f"family-wide alpha = {ALPHA}")
    print()
    header = (f"{'outcome':32s} {'placebo':>9s} {'vit D':>9s} {'test':<16s} "
              f"{'raw p':>8s} {'adj p':>8s}  verdict")
    print(header)
    print("-" * len(header))
    for r, adj, rej in zip(rows, p_adj, reject):
        verdict = "significant" if rej else "not significant"
        print(f"{r['label']:32s} {r['mean_placebo']:9.2f} {r['mean_vitd']:9.2f} "
              f"{r['test']:<16s} {r['p_raw']:8.4f} {adj:8.4f}  {verdict}")
    print()

    survivors = [r["label"] for r, rej in zip(rows, reject) if rej]
    print(f"Surviving correction: {len(survivors)} of {len(rows)}")
    for label in survivors:
        print(f"  - {label}")


if __name__ == "__main__":
    main()
