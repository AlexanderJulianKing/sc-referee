"""Generate the plaque-thickness dataset for the topical formulation study.

Twenty-four adults with chronic plaque psoriasis, twelve randomised to the
active topical formulation and twelve to the vehicle cream. Four target
plaques on different body sites were selected per patient and measured with
a calliper after eight weeks, giving 96 rows.

Standard library only. Fixed seed so the file is reproducible.
"""

import csv
import os
import random

SEED = 1324  # chosen so the realised arm means land on the specified targets
random.seed(SEED)

N_PATIENTS = 24
PLAQUES_PER_PATIENT = 4

# Week-eight induration thickness in millimetres.
ARM_MEAN_MM = {"active": 1.05, "vehicle": 1.55}
BETWEEN_PATIENT_SD_MM = 0.30   # overall severity differs clearly between patients
WITHIN_PATIENT_SD_MM = 0.25    # plaque-to-plaque scatter inside one patient
THICKNESS_MIN_MM = 0.30
THICKNESS_MAX_MM = 2.40

BODY_SITES = [
    "elbow",
    "knee",
    "scalp",
    "lower_back",
    "shin",
    "forearm",
]

AGE_MIN_YEARS = 25
AGE_MAX_YEARS = 68

# Twelve active, twelve vehicle, then shuffled across the patient list.
arms = ["active"] * 12 + ["vehicle"] * 12
random.shuffle(arms)

rows = []
for index, arm in enumerate(arms, start=1):
    patient_id = "PT%02d" % index
    age_years = random.randint(AGE_MIN_YEARS, AGE_MAX_YEARS)
    sex = random.choice(["F", "M"])

    # One severity offset per patient, shared by that patient's four plaques.
    patient_offset_mm = random.gauss(0.0, BETWEEN_PATIENT_SD_MM)
    patient_mean_mm = ARM_MEAN_MM[arm] + patient_offset_mm

    sites = random.sample(BODY_SITES, PLAQUES_PER_PATIENT)
    for site in sites:
        thickness_mm = random.gauss(patient_mean_mm, WITHIN_PATIENT_SD_MM)
        thickness_mm = min(max(thickness_mm, THICKNESS_MIN_MM), THICKNESS_MAX_MM)
        rows.append(
            {
                "patient_id": patient_id,
                "treatment_arm": arm,
                "plaque_site": site,
                "thickness_mm": round(thickness_mm, 2),
                "age_years": age_years,
                "sex": sex,
            }
        )

FIELDNAMES = [
    "patient_id",
    "treatment_arm",
    "plaque_site",
    "thickness_mm",
    "age_years",
    "sex",
]

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plaque_thickness.csv")
with open(out_path, "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print("wrote %d rows to %s" % (len(rows), out_path))
