"""Hand-hygiene prompts and nurses' skin condition.

Eight-week ward-level rollout of automated hand-hygiene prompts. Half the wards
got prompts, half carried on unchanged; nurses were assessed once at the end.
This script compares the two ward types on the five pre-listed outcomes.
"""

import pandas as pd
from scipy import stats

# Conventional five-percent significance level, used for every outcome below.
SIGNIFICANCE_LEVEL = 0.05

OUTCOMES = [
    ("hygiene_events_per_h", "hand-hygiene events per hour"),
    ("dryness_score", "clinician dryness score (0-12)"),
    ("teweloss_g_m2_h", "transepidermal water loss (g/m2/h)"),
    ("moisturiser_use_per_d", "moisturiser applications per day"),
    ("glove_hours_per_shift", "glove hours per shift"),
]


def main():
    nurses = pd.read_csv("data.csv")

    control = nurses[nurses["ward_type"] == "control"]
    prompt = nurses[nurses["ward_type"] == "prompt"]

    print("Hand-hygiene prompt trial: ward-type comparison")
    print(f"control wards: {len(control)} nurses   prompt wards: {len(prompt)} nurses")
    print(f"significance level: {SIGNIFICANCE_LEVEL}")
    print()
    print(f"{'outcome':38s} {'control':>9s} {'prompt':>9s} {'p':>10s}  verdict")

    for column, label in OUTCOMES:
        a = control[column]
        b = prompt[column]
        # Welch's t-test: the two ward groups need not have equal variance.
        t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)

        verdict = "significant" if p_value < SIGNIFICANCE_LEVEL else "not significant"

        print(f"{label:38s} {a.mean():9.2f} {b.mean():9.2f} {p_value:10.4g}  {verdict}")

    print()
    print("Positive differences favour the prompt wards for hygiene events and")
    print("moisturiser use, and indicate worse skin for dryness and water loss.")


if __name__ == "__main__":
    main()
