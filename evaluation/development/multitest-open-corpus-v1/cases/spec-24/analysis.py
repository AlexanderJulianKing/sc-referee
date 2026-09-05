"""Antibiotic-free vs conventional broiler production, one 42-day cycle.

Six production outcomes are tested between programmes, the six raw p-values are
kept in outcome order, and the whole list is handed to
statsmodels.stats.multitest.multipletests with its default correction method
and a family-wide error rate of 0.05. Only outcomes the routine rejects are
described as different between programmes.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

FAMILY_ALPHA = 0.05

OUTCOMES = [
    ("final_weight_g", "final weight, day 42 (g)"),
    ("feed_conversion", "feed conversion ratio"),
    ("breast_yield_pct", "breast yield (% carcass)"),
    ("footpad_lesion_score", "footpad lesion score (0-4)"),
    ("caecal_campylobacter_log", "caecal Campylobacter (log10 CFU/g)"),
    ("mortality_day", "mortality day"),
]


def main():
    df = pd.read_csv("data.csv")
    conv = df[df["programme"] == "conventional"]
    abf = df[df["programme"] == "antibiotic_free"]

    print("Broiler production trial, one farm, one 42-day cycle")
    print(f"  conventional     : n = {len(conv)}")
    print(f"  antibiotic_free  : n = {len(abf)}")
    print()

    raw_p = []          # kept in the same order as OUTCOMES
    means = []
    for col, _ in OUTCOMES:
        _, p = stats.ttest_ind(conv[col], abf[col])
        raw_p.append(p)
        means.append((conv[col].mean(), abf[col].mean()))

    # Default method of multipletests, whatever statsmodels ships as default.
    method = "hs"   # statsmodels default: Holm-Sidak step-down
    reject, p_adj, alpha_sidak, alpha_bonf = multipletests(raw_p, alpha=FAMILY_ALPHA)

    print(f"multipletests default method: {method} (Holm-Sidak step-down)")
    print(f"family-wide alpha = {FAMILY_ALPHA}, "
          f"single-step Sidak alpha = {alpha_sidak:.5f}, "
          f"Bonferroni alpha = {alpha_bonf:.5f}")
    print(f"all {len(raw_p)} outcomes corrected as one family")
    print()

    header = (f"{'outcome':36s} {'conventional':>13s} {'antibiotic_free':>16s} "
              f"{'raw p':>8s} {'adj p':>8s}  decision")
    print(header)
    print("-" * len(header))
    for (col, label), (m_conv, m_abf), p, adj, rej in zip(
            OUTCOMES, means, raw_p, p_adj, reject):
        decision = "different" if rej else "no difference"
        print(f"{label:36s} {m_conv:13.3f} {m_abf:16.3f} "
              f"{p:8.4f} {adj:8.4f}  {decision}")
    print()

    different = [label for (col, label), rej in zip(OUTCOMES, reject) if rej]
    if different:
        print("Outcomes the correction rejects for, i.e. different between programmes:")
        for label in different:
            print(f"  - {label}")
    else:
        print("No outcome is rejected after correction.")


if __name__ == "__main__":
    main()
