"""Sourdough vs commercial yeast: six bread quality outcomes over 70 bakes.

Six outcomes are tested, so the six p-values are treated as one family and put
through a single Holm step-down correction. Holm controls the family-wise error
rate, i.e. the chance of making even one false claim across the six.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

METHOD = "holm"
METHOD_LABEL = "Holm-Bonferroni step-down (family-wise error rate)"
ALPHA = 0.05

OUTCOMES = [
    "specific_volume_ml_g",
    "crumb_hardness_n",
    "staling_rate_n_per_day",
    "ph_final",
    "phytate_mg_100g",
    "sensory_sourness",
]

loaves = pd.read_csv("data.csv")
yeast = loaves[loaves["process"] == "yeast"]
sourdough = loaves[loaves["process"] == "sourdough"]

print("loaves: %d (yeast %d, sourdough %d)"
      % (len(loaves), len(yeast), len(sourdough)))

raw_p = []
summary = []
for name in OUTCOMES:
    a = yeast[name]
    b = sourdough[name]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    raw_p.append(p)
    summary.append((name, a.mean(), b.mean()))

reject, p_adj, alpha_sidak, alpha_bonf = multipletests(
    raw_p, alpha=ALPHA, method=METHOD)

print("correction: %s" % METHOD_LABEL)
print("family: all %d quality outcomes, corrected in one pass at alpha = %.2f"
      % (len(raw_p), ALPHA))
print()
print("%-24s %10s %10s %12s %12s  %s"
      % ("outcome", "yeast", "sourdough", "raw p", "Holm p", "verdict"))
for i, (name, yeast_mean, sour_mean) in enumerate(summary):
    verdict = "significant" if reject[i] else "not significant"
    print("%-24s %10.3f %10.3f %12.3e %12.3e  %s"
          % (name, yeast_mean, sour_mean, raw_p[i], p_adj[i], verdict))

print()
print("survives Holm correction: %d of %d outcomes"
      % (sum(bool(r) for r in reject), len(OUTCOMES)))
