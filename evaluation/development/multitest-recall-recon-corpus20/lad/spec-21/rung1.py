"""Enrichment housing for laboratory rabbits: welfare and physiology at eight weeks.

Six outcomes are compared between standard cages and enriched pens. Faecal
corticosterone and stereotypy bouts were nominated in the protocol as the two
welfare-critical outcomes, so those two are corrected as their own small family
(Holm, family alpha 0.05). The remaining four outcomes are reported against the
plain 0.05 level.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

OUTCOMES = [
    ("body_weight_g", "final body weight (g)"),
    ("faecal_cort_ng_g", "faecal corticosterone (ng/g)"),
    ("stereotypy_bouts_h", "stereotypy bouts (per h)"),
    ("bone_density_mg_cm3", "femoral bone density (mg/cm3)"),
    ("sole_lesion_score", "sole lesion score (0-6)"),
    ("latency_to_feed_s", "latency to novel food (s)"),
]

WELFARE_CRITICAL = ["faecal_cort_ng_g", "stereotypy_bouts_h"]


def main():
    df = pd.read_csv("data.csv")
    standard = df[df["housing"] == "standard"]
    enriched = df[df["housing"] == "enriched"]

    print("Enrichment housing trial")
    print(f"  standard cages : n = {len(standard)}")
    print(f"  enriched pens  : n = {len(enriched)}")
    print()

    # Two-sample test for a difference in means, one per outcome.
    results = {}
    for col, label in OUTCOMES:
        t_stat, p = stats.ttest_ind(standard[col], enriched[col])
        results[col] = {
            "label": label,
            "mean_standard": standard[col].mean(),
            "mean_enriched": enriched[col].mean(),
            "t": t_stat,
            "p_raw": p,
        }

    # The two protocol-nominated welfare outcomes form their own family.
    critical_p = [results[col]["p_raw"] for col in WELFARE_CRITICAL]
    reject, p_holm, _, _ = multipletests(critical_p, alpha=ALPHA, method="holm")
    for col, rej, p_adj in zip(WELFARE_CRITICAL, reject, p_holm):
        results[col]["p_reported"] = p_adj
        results[col]["basis"] = "Holm-adjusted"
        results[col]["significant"] = bool(rej)

    # The four secondary outcomes are read straight off their raw p-values.
    for col, _ in OUTCOMES:
        if col in WELFARE_CRITICAL:
            continue
        results[col]["p_reported"] = results[col]["p_raw"]
        results[col]["basis"] = "raw"
        results[col]["significant"] = results[col]["p_raw"] < ALPHA

    print("Holm correction applied to the welfare-critical family "
          f"({', '.join(WELFARE_CRITICAL)}), family alpha = {ALPHA}.")
    print("The four secondary outcomes are judged on their raw p-values.")
    print()

    header = f"{'outcome':30s} {'standard':>10s} {'enriched':>10s} {'p':>9s}  {'basis':<14s} verdict"
    print(header)
    print("-" * len(header))
    for col, _ in OUTCOMES:
        r = results[col]
        verdict = "significant" if r["significant"] else "not significant"
        print(f"{r['p_reported']:9.4f}  {verdict}")
    print()

    called = [results[c]["label"] for c, _ in OUTCOMES if results[c]["significant"]]
    print(f"Outcomes differing between housing types: {len(called)} of {len(OUTCOMES)}")
    for label in called:
        print(f"  - {label}")


if __name__ == "__main__":
    main()
