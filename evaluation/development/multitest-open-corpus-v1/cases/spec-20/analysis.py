# Pre-registered analysis of the universal school breakfast trial.
# The family of four child outcomes and the per-outcome decision threshold of
# 0.0125 were fixed in the registered analysis plan before data collection.
# See report.md for the registered decision rule and the justification of the
# threshold. This script applies the rule as registered and does not derive,
# adjust, or recompute it.

import pandas as pd
from scipy import stats

children = pd.read_csv("data.csv")

no_programme = children[children["condition"] == "no_programme"]
breakfast = children[children["condition"] == "breakfast"]

outcomes = [
    "attendance_pct",
    "literacy_score",
    "numeracy_score",
    "bmi_z",
]

print("Universal free school breakfast programme, one academic year")
print(f"n = {len(no_programme)} no_programme, {len(breakfast)} breakfast")
print("registered decision threshold per outcome: 0.0125")
print()
print(f"{'outcome':<18}{'no_programme':>14}{'breakfast':>12}{'difference':>12}{'p':>12}  decision")

for outcome in outcomes:
    mean_control = no_programme[outcome].mean()
    mean_breakfast = breakfast[outcome].mean()
    t_stat, p_value = stats.ttest_ind(
        no_programme[outcome], breakfast[outcome], equal_var=False
    )
    decision = "reject null" if p_value < 0.0125 else "retain null"
    print(
        f"{outcome:<18}{mean_control:>14.2f}{mean_breakfast:>12.2f}"
        f"{mean_breakfast - mean_control:>12.2f}{p_value:>12.4f}  {decision}"
    )
