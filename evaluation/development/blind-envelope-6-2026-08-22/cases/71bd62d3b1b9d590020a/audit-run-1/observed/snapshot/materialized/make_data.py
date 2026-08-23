"""Generate the simulated force-platform dataset for the canine elbow
osteoarthritis analgesic comparison.

Design: 24 client-owned dogs, 12 per treatment arm, each measured at
5 visits (baseline, weeks 2, 4, 8, 12). Outcome is peak vertical force
through the affected forelimb as a percentage of body weight.

Standard library only. Fixed seed so the CSV is reproducible.
Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822
N_PER_ARM = 12
VISIT_WEEKS = [0, 2, 4, 8, 12]

# Mean trajectory: 60 %BW at baseline in both arms, rising along a
# saturating curve gain * week / (week + HALF_K).
BASELINE_MEAN = 60.0
HALF_K = 4.0
# gain chosen so week-12 mean is 66 %BW (established) and 71 %BW (new)
ARM_GAIN = {
    "established": 6.0 * (12.0 + HALF_K) / 12.0,   # -> +6.0 %BW at week 12
    "new": 11.0 * (12.0 + HALF_K) / 12.0,          # -> +11.0 %BW at week 12
}

DOG_SD = 3.0        # persistent dog-to-dog differences in force
RESID_SD = 1.2      # visit-to-visit measurement noise
WEIGHT_MIN, WEIGHT_MAX = 18.0, 42.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pvf_repeated_measures.csv")


def mean_force(arm, week):
    return BASELINE_MEAN + ARM_GAIN[arm] * week / (week + HALF_K)


def main():
    rng = random.Random(SEED)
    rows = []

    dogs = []
    for i in range(N_PER_ARM):
        dogs.append(("established", "D%02d" % (2 * i + 1)))
        dogs.append(("new", "D%02d" % (2 * i + 2)))
    dogs.sort(key=lambda d: d[1])

    for arm, dog_id in dogs:
        dog_effect = rng.gauss(0.0, DOG_SD)
        base_weight = rng.uniform(WEIGHT_MIN + 0.5, WEIGHT_MAX - 0.5)
        for week in VISIT_WEEKS:
            weight = base_weight + rng.gauss(0.0, 0.35)
            weight = min(max(weight, WEIGHT_MIN), WEIGHT_MAX)
            pvf = mean_force(arm, week) + dog_effect + rng.gauss(0.0, RESID_SD)
            rows.append({
                "dog_id": dog_id,
                "treatment_arm": arm,
                "visit_week": week,
                "body_weight_kg": round(weight, 1),
                "peak_vertical_force_pctbw": round(pvf, 2),
            })

    fields = ["dog_id", "treatment_arm", "visit_week",
              "body_weight_kg", "peak_vertical_force_pctbw"]
    with open(OUT_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d data rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
