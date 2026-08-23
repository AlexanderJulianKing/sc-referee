"""Generate the pre-dialysis serum phosphate dataset for the binder study.

Standard library only. Fixed seed, so re-running reproduces phosphate_data.csv
byte for byte.

Design: 18 prevalent haemodialysis patients, 9 on each oral phosphate binder,
sampled before the mid-week dialysis session on 8 consecutive study weeks.
18 patients x 8 weeks = 144 rows.

Generating model for the phosphate value of patient i in week w:

    phosphate = arm_mean[arm(i)] + patient_effect[i] + week_noise[i, w]

    arm_mean  = 1.90 mmol/L (established binder), 1.55 mmol/L (newer binder)
    patient_effect ~ Normal(0, 0.35)   between-patient variation
    week_noise     ~ Normal(0, 0.18)   within-patient week-to-week variation

Values are rounded to 2 decimal places, as a hospital laboratory reports them,
and clamped to the clinically plausible window 0.90 - 2.80 mmol/L. With this
seed the generated values already fall inside that window, so the clamp never
changes a value; it is kept only as a guard.
"""

import csv
import os
import random

SEED = 20260952

N_PATIENTS_PER_ARM = 9
N_WEEKS = 8

ARMS = [
    # (label written into the csv, arm mean in mmol/L)
    ("calcium_acetate", 1.90),           # established binder
    ("sucroferric_oxyhydroxide", 1.55),  # newer binder
]

BETWEEN_PATIENT_SD = 0.35
WITHIN_PATIENT_SD = 0.18

LOWER_LIMIT = 0.90
UPPER_LIMIT = 2.80

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "phosphate_data.csv")


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Patients are numbered in a single sequence and alternate between the two
    # binder arms, the way consecutive consenting patients were allocated.
    patients = []
    for pair_index in range(N_PATIENTS_PER_ARM):
        for arm_label, arm_mean in ARMS:
            patient_number = len(patients) + 1
            patients.append({
                "patient_id": "HD-{:02d}".format(patient_number),
                "binder_regimen": arm_label,
                "arm_mean": arm_mean,
                "patient_effect": rng.gauss(0.0, BETWEEN_PATIENT_SD),
            })

    rows = []
    for patient in patients:
        for week in range(1, N_WEEKS + 1):
            raw = (patient["arm_mean"]
                   + patient["patient_effect"]
                   + rng.gauss(0.0, WITHIN_PATIENT_SD))
            value = clamp(round(raw, 2), LOWER_LIMIT, UPPER_LIMIT)
            rows.append({
                "patient_id": patient["patient_id"],
                "binder_regimen": patient["binder_regimen"],
                "study_week": week,
                "serum_phosphate_mmol_l": "{:.2f}".format(value),
            })

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["patient_id", "binder_regimen", "study_week",
                        "serum_phosphate_mmol_l"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} ({} rows)".format(OUT_PATH, len(rows)))


if __name__ == "__main__":
    main()
