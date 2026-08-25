"""Weaning trial: basal creep feed vs the same feed with a Bacillus probiotic.

96 piglets, 48 per diet, one row per piglet, 28 days on test.
"""

import pandas as pd
from scipy import stats

data = pd.read_csv("data.csv")
basal = data[data["diet"] == "basal"]
probiotic = data[data["diet"] == "probiotic"]

outcomes = [
    "adg_g_d",
    "feed_conversion",
    "diarrhoea_days",
    "faecal_lactobacilli_log",
    "serum_iga_mg_l",
]

pvalues = [stats.ttest_ind(basal[o], probiotic[o], equal_var=False).pvalue for o in outcomes]
verdicts = ["significant" if p < 0.05 else "not significant" for p in pvalues]

print(f"n = {len(basal)} basal, {len(probiotic)} probiotic\n")
print(f"{'outcome':<26}{'basal':>10}{'probiotic':>12}{'p':>10}  verdict")
for outcome, p, verdict in zip(outcomes, pvalues, verdicts):
    print(f"{outcome:<26}{basal[outcome].mean():>10.2f}{probiotic[outcome].mean():>12.2f}"
          f"{p:>10.4f}  {verdict}")
