"""Day-12 nestling mass in supplemented vs. control great tit broods."""

import pandas as pd
from scipy import stats

# Load the day-12 field records.
data = pd.read_csv("nestling_mass.csv")

# Split the nestling masses by the feeding treatment its box received.
supplemented = data.loc[data["food_treatment"] == "supplemented", "mass_g_day12"]
control = data.loc[data["food_treatment"] == "control", "mass_g_day12"]

# Two-sample t-test on the individual nestling masses.
t_stat, p_value = stats.ttest_ind(supplemented, control)

print("Day-12 nestling mass (g)")
print("------------------------")
for label, values in (("supplemented", supplemented), ("control", control)):
    print(
        f"{label:>13}: n = {len(values):d}, "
        f"mean = {values.mean():.2f} g, "
        f"SD = {values.std(ddof=1):.2f} g"
    )

print()
print(f"difference (supplemented - control) = {supplemented.mean() - control.mean():.2f} g")
print(f"t = {t_stat:.3f}")
print(f"p = {p_value:.6f}")
