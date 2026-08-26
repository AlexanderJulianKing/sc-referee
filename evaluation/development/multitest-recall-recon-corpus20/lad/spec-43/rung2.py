"""Weaner diet trial: organic acid / essential oil blend against pharmacological ZnO.

One weaning batch, 100 pigs, 35 days on test. Final weight, average daily gain and
feed conversion were pre-specified as the performance family and are corrected
together at a five percent family level. Diarrhoea score, faecal zinc and villus
height are supporting measures reported at the plain five percent level.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05

PERFORMANCE = [
    ("final_weight_kg", "Final weight (kg)"),
    ("adg_g_d", "Average daily gain (g/d)"),
    ("feed_conversion", "Feed conversion (feed:gain)"),
]

SUPPORTING = [
    ("diarrhoea_score", "Diarrhoea score (0-3)"),
    ("faecal_zinc_mg_kg", "Faecal zinc (mg/kg DM)"),
    ("villus_height_um", "Jejunal villus height (um)"),
]


def two_sample_p(control, test, column):
    _, p = stats.ttest_ind(control[column], test[column])
    return p


def fmt_p(p):
    return "<0.0001" if p < 0.0001 else "%.4f" % p


df = pd.read_csv("data.csv")
zn = df[df["diet"] == "zinc_oxide"]
ab = df[df["diet"] == "acid_blend"]

perf_raw = [two_sample_p(zn, ab, c) for c, _ in PERFORMANCE]
_, perf_adj, _, _ = multipletests(perf_raw, alpha=ALPHA, method="holm")
supp_raw = [two_sample_p(zn, ab, c) for c, _ in SUPPORTING]

print("Zinc oxide replacement trial, n = %d zinc oxide, %d acid blend" % (len(zn), len(ab)))
print("Performance family (3 outcomes) corrected with Holm at family alpha = %.2f" % ALPHA)
print("Supporting measures judged at alpha = %.2f" % ALPHA)
print()
print("%-30s %12s %12s %10s  %s" % ("Outcome", "zinc oxide", "acid blend", "p-value", "Result"))
print("-" * 84)

for (column, label), p in zip(PERFORMANCE, perf_adj):
    result = "significant" if p < ALPHA else "not significant"
    print(f"{label:-30s} {zn[column].mean():12.2f} {ab[column].mean():12.2f} {p:10.4f}  {result}")

for (column, label), p in zip(SUPPORTING, supp_raw):
    result = "significant" if p < ALPHA else "not significant"
    print(f"{label:-30s} {zn[column].mean():12.2f} {ab[column].mean():12.2f} {p:10.4f}  {result}")

print()
print("Unadjusted p-values for the performance family reported above.")
