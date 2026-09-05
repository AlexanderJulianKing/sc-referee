"""Telehealth versus in-person follow-up after total hip replacement.

Six outcomes collected at the twelve-week review, one row per patient.
Each outcome is compared with a Welch two-sample t-test and reported on its
own line.
"""

import pandas as pd
from scipy import stats

patients = pd.read_csv("data.csv")

in_person = patients[patients["pathway"] == "in_person"]
telehealth = patients[patients["pathway"] == "telehealth"]

outcomes = [
    "oxford_hip_score",
    "pain_vas",
    "physio_sessions",
    "readmission_days",
    "travel_cost_gbp",
    "satisfaction_score",
]

print("Twelve-week review after elective total hip replacement")
print(f"n = {len(in_person)} in-person, {len(telehealth)} telehealth")
print()

for outcome in outcomes:
    mean_in_person = in_person[outcome].mean()
    mean_telehealth = telehealth[outcome].mean()
    t_stat, p_value = stats.ttest_ind(
        in_person[outcome], telehealth[outcome], equal_var=False
    )
    print(
        f"{outcome:<20} in-person {mean_in_person:8.2f}   "
        f"telehealth {mean_telehealth:8.2f}   "
        f"difference {mean_telehealth - mean_in_person:8.2f}   "
        f"p = {p_value:.4g}   "
        f"{'statistically significant' if p_value < 0.05 else 'no significant difference'}"
    )
