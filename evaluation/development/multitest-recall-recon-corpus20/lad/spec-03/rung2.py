"""HEPA filtration in classrooms: filtered vs unfiltered rooms, one row per pupil.

Five outcomes, each tested and judged as it comes round in the loop.
"""

import pandas as pd
from scipy import stats

OUTCOMES = [
    "pm25_exposure_ug_m3",
    "peak_flow_l_min",
    "cough_days",
    "absence_days",
    "feno_ppb",
]

pupils = pd.read_csv("data.csv")

print("pupils: %d" % len(pupils))
print(pupils["room_type"].value_counts().to_string())
print()

for outcome in OUTCOMES:
    filtered = pupils.loc[pupils["room_type"] == "filtered", outcome]
    unfiltered = pupils.loc[pupils["room_type"] == "unfiltered", outcome]
    t, p = stats.ttest_ind(filtered, unfiltered, equal_var=False)
    verdict = "significant" if p < 0.05 else "not significant"
    print(f"{outcome:-22s} unfiltered {unfiltered.mean():8.2f}   filtered {filtered.mean():8.2f}   p = {p:.4f}   {verdict}")
