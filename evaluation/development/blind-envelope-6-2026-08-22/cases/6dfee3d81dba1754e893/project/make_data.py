"""Generate the six-minute walk test dataset for the knee rehabilitation study.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design: 44 patients, 22 per rehabilitation protocol. Each patient performs the
six-minute walk test once, at the three-month follow-up, so the file has exactly
one row per patient and no repeated patient_ref values.

Outcome model (metres walked in six minutes):

    six_min_walk_m = base(protocol)
                     + age_slope  * (age_years - 70)
                     + bmi_slope  * (bmi - 30)
                     + residual noise

with base = 415 m for standard supervised outpatient physiotherapy and 448 m for
the home-based programme with weekly telephone coaching. Older and heavier
patients walk somewhat shorter distances (both slopes are negative). The residual
standard deviation is chosen so that the total between-patient standard deviation
inside a protocol is about 60 m.
"""

import csv
import math
import os
import random

SEED = 20260822
N_PER_ARM = 22

PROTOCOLS = [
    ("standard_outpatient", 415.0),
    ("home_based_telephone", 448.0),
]

AGE_MIN, AGE_MAX = 58.0, 82.0
BMI_MIN, BMI_MAX = 22.0, 38.0

AGE_CENTRE = 70.0
BMI_CENTRE = 30.0

AGE_SLOPE = -1.6   # metres lost per extra year of age
BMI_SLOPE = -3.0   # metres lost per extra BMI unit

TARGET_SD = 60.0   # total between-patient SD wanted inside one protocol


def residual_sd():
    """Residual SD that leaves the total between-patient SD near TARGET_SD."""
    age_sd = (AGE_MAX - AGE_MIN) / math.sqrt(12.0)
    bmi_sd = (BMI_MAX - BMI_MIN) / math.sqrt(12.0)
    explained_var = (AGE_SLOPE * age_sd) ** 2 + (BMI_SLOPE * bmi_sd) ** 2
    return math.sqrt(max(TARGET_SD ** 2 - explained_var, 1.0))


def main():
    rng = random.Random(SEED)
    sigma = residual_sd()

    rows = []
    for protocol, base in PROTOCOLS:
        for _ in range(N_PER_ARM):
            age = rng.uniform(AGE_MIN, AGE_MAX)
            bmi = rng.uniform(BMI_MIN, BMI_MAX)
            distance = (
                base
                + AGE_SLOPE * (age - AGE_CENTRE)
                + BMI_SLOPE * (bmi - BMI_CENTRE)
                + rng.gauss(0.0, sigma)
            )
            distance = min(max(distance, 180.0), 640.0)
            rows.append(
                {
                    "rehab_protocol": protocol,
                    "age_years": round(age, 1),
                    "bmi": round(bmi, 1),
                    "six_min_walk_m": round(distance, 1),
                }
            )

    # Shuffle so the two protocols are interleaved rather than blocked, then
    # label patients in file order. One patient_ref appears exactly once.
    rng.shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["patient_ref"] = "PT-{:03d}".format(index)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knee_rehab_6mwt.csv")
    fields = ["patient_ref", "rehab_protocol", "age_years", "bmi", "six_min_walk_m"]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})

    print("wrote {} rows to {}".format(len(rows), out_path))
    print("residual sd used: {:.2f} m".format(sigma))


if __name__ == "__main__":
    main()
