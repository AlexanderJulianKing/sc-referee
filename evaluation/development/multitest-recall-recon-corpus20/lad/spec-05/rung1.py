"""Riparian buffer width and stream condition: 26 narrow vs 26 wide reaches.

Six outcomes, walked through by position so the printed numbering matches the
slot each p-value is stored in.
"""

import pandas as pd
from scipy import stats

OUTCOMES = [
    "turbidity_ntu",
    "total_p_mg_l",
    "nitrate_mg_l",
    "water_temp_c",
    "macroinvert_ept_taxa",
    "canopy_cover_pct",
]

reaches = pd.read_csv("data.csv")
print("reaches: %d" % len(reaches))
print(reaches["buffer_class"].value_counts().to_string())
print()

pvalues = [None] * len(OUTCOMES)
narrow_means = [None] * len(OUTCOMES)
wide_means = [None] * len(OUTCOMES)

for position, outcome in enumerate(OUTCOMES):
    narrow = reaches.loc[reaches["buffer_class"] == "narrow", outcome]
    wide = reaches.loc[reaches["buffer_class"] == "wide", outcome]

    t, p = stats.ttest_ind(narrow, wide, equal_var=False)
    pvalues[position] = p
    narrow_means[position] = narrow.mean()
    wide_means[position] = wide.mean()

    if p < 0.05:
        verdict = "significant"
    else:
        verdict = "not significant"

    print("%d. %-22s narrow %9.3f   wide %9.3f   p = %.4f   %s"
          % (position + 1, outcome, narrow.mean(), wide.mean(), p, verdict))


print()
print("significant outcomes: %d of %d"
      % (sum(1 for p in pvalues if p < 0.05), len(OUTCOMES)))
