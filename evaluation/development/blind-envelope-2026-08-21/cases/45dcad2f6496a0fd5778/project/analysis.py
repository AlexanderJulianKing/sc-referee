"""Novel-tank swimming activity after 14-day low-dose fluoxetine exposure.

Compares total distance moved between control and fluoxetine-exposed
adult zebrafish.
"""

import pandas as pd
from scipy import stats

# Load the recorded trials: one row per fish.
df = pd.read_csv("zebrafish_activity.csv")

# Split the distances by water condition.
control = df.loc[df["exposure"] == "control", "distance_cm"]
fluoxetine = df.loc[df["exposure"] == "fluoxetine", "distance_cm"]

# Descriptive statistics for each condition.
for name, values in (("control", control), ("fluoxetine", fluoxetine)):
    print(
        f"{name}: n = {values.size}, "
        f"mean = {values.mean():.1f} cm, "
        f"SD = {values.std(ddof=1):.1f} cm"
    )

# Two-sample t-test on the individual fish measurements.
t_stat, p_value = stats.ttest_ind(control, fluoxetine)

print(f"t = {t_stat:.3f}")
print(f"p = {p_value:.4f}")
print(f"mean difference (control - fluoxetine) = {control.mean() - fluoxetine.mean():.1f} cm")
