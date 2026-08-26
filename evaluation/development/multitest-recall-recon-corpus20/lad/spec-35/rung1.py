"""Tree canopy cover and summer emergency department visits, 60 city neighbourhoods.

30 low-canopy and 30 high-canopy neighbourhoods, one summary row each, from one
summer of routine health and environmental data.

The file is in two stages. The testing stage does all the arithmetic and stores it;
it prints nothing, so that nothing about how the numbers look can feed back into how
they were produced. The reporting stage reads the stored results back in the declared
outcome order and formats them.

Run from this directory:  python analysis.py
"""

import pandas as pd
from scipy import stats

OUTCOMES = [
    ("mean_summer_temp_c", "mean summer temp (C)"),
    ("heat_ed_visits_per_1000", "heat ED visits /1000"),
    ("asthma_ed_visits_per_1000", "asthma ED visits /1000"),
    ("night_temp_c", "night min temp (C)"),
    ("pm25_annual_ug_m3", "annual PM2.5 (ug/m3)"),
]

SIGNIFICANCE_CUTOFF = 0.05

neighbourhoods = pd.read_csv("data.csv")
low_canopy = neighbourhoods[neighbourhoods["canopy_class"] == "low"]
high_canopy = neighbourhoods[neighbourhoods["canopy_class"] == "high"]


# --- testing stage: compute and store, print nothing --------------------------
results = {}
for column, label in OUTCOMES:
    low_values = low_canopy[column]
    high_values = high_canopy[column]
    t_stat, p_value = stats.ttest_ind(low_values, high_values, equal_var=False)
    results[column] = {
        "label": label,
        "low_mean": low_values.mean(),
        "high_mean": high_values.mean(),
        "p_value": p_value,
    }


# --- reporting stage: read the stored results back and format them ------------
print("Urban heat and emergency department visits by neighbourhood")
print(f"{len(neighbourhoods)} neighbourhoods: {len(low_canopy)} low canopy, "
      f"{len(high_canopy)} high canopy")
print()
print(f"{'outcome':24s} {'low':>8s} {'high':>8s} {'difference':>11s} {'p':>11s}  verdict")

for column, _ in OUTCOMES:
    result = results[column]
    significant = result["p_value"] < SIGNIFICANCE_CUTOFF
    verdict = "significant" if significant else "not significant"
    print(
        f"{result['label']:24s} {result['low_mean']:8.2f} {result['high_mean']:8.2f} "
        f"{result['p_value']:11.4g}  {verdict}"
    )

print()
print(f"Differences are low canopy minus high canopy. Cutoff: p < {SIGNIFICANCE_CUTOFF}.")
