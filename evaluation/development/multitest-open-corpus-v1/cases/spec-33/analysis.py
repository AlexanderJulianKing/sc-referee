"""Sit-stand desks vs fixed desks: activity and musculoskeletal outcomes at 3 months.

104 office staff, 52 on floors that received sit-stand desks and 52 on comparable
floors that kept fixed desks. One row per employee.

The six outcomes are listed once, in the order they were collected, and the loop
below walks that list and tests each one.

Run from this directory:  python analysis.py
"""

import pandas as pd
from scipy import stats

OUTCOMES = [
    "sitting_hours_per_day",
    "standing_hours_per_day",
    "low_back_pain_score",
    "neck_pain_score",
    "fatigue_score",
    "productivity_self",
]

staff = pd.read_csv("data.csv")
fixed = staff[staff["desk_type"] == "fixed"]
sit_stand = staff[staff["desk_type"] == "sit_stand"]

print("Standing desks in an office population - three-month follow-up")
print(f"{len(staff)} employees: {len(fixed)} fixed desk, {len(sit_stand)} sit-stand desk")
print()
print(f"{'outcome':24s} {'fixed':>8s} {'sit_stand':>10s} {'p':>10s}  below 0.05?")

for outcome in OUTCOMES:
    fixed_values = fixed[outcome]
    sit_stand_values = sit_stand[outcome]
    t_stat, p_value = stats.ttest_ind(fixed_values, sit_stand_values, equal_var=False)
    below_cutoff = "yes" if p_value < 0.05 else "no"
    print(
        f"{outcome:24s} {fixed_values.mean():8.2f} {sit_stand_values.mean():10.2f} "
        f"{p_value:10.4g}  {below_cutoff}"
    )
