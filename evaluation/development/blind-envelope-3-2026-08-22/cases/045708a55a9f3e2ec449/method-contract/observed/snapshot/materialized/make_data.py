"""Generate the transport-stress cortisol dataset for the equine study.

Twenty horses from one riding centre: ten transported on a four-hour road journey,
ten kept in the home yard. One blood sample per horse, drawn two hours after the
transported group returned. Each sample was assayed for serum cortisol in
triplicate on the same plate, so each horse contributes three rows.

Run with a fixed seed so the file is reproducible:
    python3 make_data.py
"""

import csv
import os
import random

# Fixed seed. This particular value was chosen so that the drawn group means and
# the between-horse spread land close to the intended study values below.
SEED = 57704

# Group means for serum cortisol, nmol/L
MEAN_TRANSPORTED = 118.0
MEAN_STAYED = 74.0

# Spread between animals within a group, nmol/L
SD_BETWEEN_HORSES = 22.0

# Spread among the three assay replicates of a single sample, nmol/L
SD_WITHIN_SAMPLE = 6.0

N_PER_GROUP = 10
N_REPLICATES = 3

OUT_NAME = "cortisol_transport.csv"

FIELDNAMES = [
    "horse_id",
    "transport_condition",
    "replicate",
    "cortisol_nmol_l",
    "age_years",
]


def build_rows(rng):
    rows = []
    horse_number = 0

    for condition, group_mean in (
        ("transported", MEAN_TRANSPORTED),
        ("stayed", MEAN_STAYED),
    ):
        for _ in range(N_PER_GROUP):
            horse_number += 1
            horse_id = "H{:02d}".format(horse_number)

            # Age of the animal, whole years, typical riding-centre range.
            age_years = int(round(rng.gauss(12.0, 3.6)))
            age_years = max(4, min(22, age_years))

            # True cortisol concentration of this horse's sample.
            true_value = rng.gauss(group_mean, SD_BETWEEN_HORSES)
            true_value = max(15.0, true_value)

            for replicate in range(1, N_REPLICATES + 1):
                # Assay noise: three measurements of the same tube of serum.
                reading = rng.gauss(true_value, SD_WITHIN_SAMPLE)
                reading = max(5.0, reading)

                rows.append(
                    {
                        "horse_id": horse_id,
                        "transport_condition": condition,
                        "replicate": replicate,
                        "cortisol_nmol_l": round(reading, 1),
                        "age_years": age_years,
                    }
                )

    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
