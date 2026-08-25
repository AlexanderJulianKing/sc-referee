"""Cold-water immersion versus passive rest after competitive matches.

Five recovery markers measured 24 h post-match, one match per player.
Welch two-sample t-test on each marker.
"""

import pandas as pd
from scipy import stats

data = pd.read_csv("data.csv")

passive = data[data["recovery"] == "passive"]
cold_water = data[data["recovery"] == "cold_water"]

outcomes = [
    "ck_u_l",
    "soreness_vas",
    "cmj_height_cm",
    "sprint_20m_s",
    "sleep_quality",
]

print("Cold-water immersion vs passive rest, 24 h post-match")
print(f"n = {len(passive)} passive, {len(cold_water)} cold_water")
print()
print(f"{'outcome':<16}{'passive':>10}{'cold_water':>12}{'difference':>12}{'p':>12}  verdict")

for outcome in outcomes:
    mean_passive = passive[outcome].mean()
    mean_cold = cold_water[outcome].mean()
    difference = mean_cold - mean_passive
    t_stat, p_value = stats.ttest_ind(
        passive[outcome], cold_water[outcome], equal_var=False
    )
    if p_value < 0.05:
        verdict = "significant"
    else:
        verdict = "not significant"
    print(
        f"{outcome:<16}{mean_passive:>10.2f}{mean_cold:>12.2f}"
        f"{difference:>12.2f}{p_value:>12.3e}  {verdict}"
    )
