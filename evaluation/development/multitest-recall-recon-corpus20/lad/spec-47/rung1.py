"""Finished-water quality at two small works, one with a granular activated
carbon stage and one without.

96 routine finished-water samples over one year, 48 per works. Six outcomes are
reported. Total trihalomethanes and the five haloacetic acids are the regulated
disinfection by-products and were pre-specified as the regulatory pair, so they
are judged against a Bonferroni threshold of 0.05 / 2. The four operational
outcomes are judged against the plain 0.05 level.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05
REGULATORY = ["total_thm_ug_l", "haa5_ug_l"]
BONFERRONI_THRESHOLD = ALPHA / len(REGULATORY)

OUTCOMES = [
    ("total_thm_ug_l", "total THMs (ug/L)", 1),
    ("haa5_ug_l", "HAA5 (ug/L)", 1),
    ("toc_mg_l", "TOC (mg/L)", 2),
    ("turbidity_ntu", "turbidity (NTU)", 3),
    ("free_chlorine_mg_l", "free chlorine (mg/L)", 2),
    ("taste_odour_ton", "threshold odour number", 1),
]


def fmt_p(p):
    return f"{p:.2e}" if p < 1e-4 else f"{p:.5f}"


def main():
    data = pd.read_csv("data.csv")
    conventional = data[data["works_type"] == "conventional"]
    gac = data[data["works_type"] == "gac_added"]
    print(f"Samples: conventional n={len(conventional)}, gac_added n={len(gac)}")
    print("Test: two-sample Welch t-test on the difference in means, two sided.")
    print(f"Regulatory pair {REGULATORY} judged at {ALPHA} / {len(REGULATORY)} "
          f"= {BONFERRONI_THRESHOLD:.4f} (Bonferroni, computed here by hand).")
    print(f"Operational outcomes judged at {ALPHA:.2f}, uncorrected.\n")

    header = (f"{'outcome':<24}{'conventional':>14}{'gac_added':>12}{'diff':>10}"
              f"{'p':>12}{'threshold':>11}  result")
    print(header)
    print("-" * len(header))

    for column, label, dp in OUTCOMES:
        a = conventional[column]
        b = gac[column]
        p = stats.ttest_ind(a, b, equal_var=False).pvalue
        threshold = BONFERRONI_THRESHOLD if column in REGULATORY else ALPHA
        verdict = "significant" if p < threshold else "not significant"
        print(f"{label:<24}{a.mean():>14.{dp}f}{b.mean():>12.{dp}f}"
              f"{a.mean() - b.mean():>10.{dp}f}{p:>12.5f}{threshold:>11.4f}  {verdict}")

    print()
    print("Threshold column shows which level each outcome was judged against.")


if __name__ == "__main__":
    main()
