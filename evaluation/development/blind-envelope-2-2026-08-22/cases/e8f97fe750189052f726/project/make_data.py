"""Generate the wing-size data set for the Drosophila high-sugar diet experiment.

Design
------
16 rearing vials are the experimental units: 8 vials on standard cornmeal-molasses
medium and 8 vials on the same medium with added sucrose. Diet is assigned to the
whole vial. After eclosion, 12 adult female flies are sampled from each vial and one
wing per fly is mounted and measured, giving 192 measured flies in total.

Generative model
----------------
    wing_centroid_size_mm[i,j] = diet_mean[diet(i)] + vial_effect[i] + fly_noise[i,j]

    diet_mean["standard"]   = 2.42 mm
    diet_mean["high_sugar"] = 2.31 mm
    vial_effect  ~ Normal(0, 0.05)   (between-vial SD, one draw per vial)
    fly_noise    ~ Normal(0, 0.07)   (within-vial SD, one draw per fly)

Measurements are rounded to three decimal places. Standard library only; the seed is
fixed so the CSV is reproducible.

Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822
OUTPUT_CSV = "wing_size.csv"

N_VIALS_PER_DIET = 8
N_FLIES_PER_VIAL = 12

DIET_MEANS = {"standard": 2.42, "high_sugar": 2.31}
BETWEEN_VIAL_SD = 0.05
WITHIN_VIAL_SD = 0.07

MEASUREMENT_DAYS = (3, 4, 5)

COLUMNS = [
    "vial_id",
    "diet",
    "fly_id",
    "wing_centroid_size_mm",
    "day_after_eclosion",
]


def build_rows(rng):
    """Return one row per measured fly, ordered V01..V16 and F01..F12 within a vial."""
    # Diets are laid out so the two groups interleave across the vial numbering,
    # which is how the vials were spread across incubator shelves.
    diets = ["standard", "high_sugar"] * N_VIALS_PER_DIET
    rows = []

    for vial_index, diet in enumerate(diets, start=1):
        vial_id = "V{:02d}".format(vial_index)
        vial_effect = rng.gauss(0.0, BETWEEN_VIAL_SD)

        # Each vial was scored in one sitting, so its flies cluster on one or two days.
        first_day = rng.choice(MEASUREMENT_DAYS)

        for fly_index in range(1, N_FLIES_PER_VIAL + 1):
            fly_noise = rng.gauss(0.0, WITHIN_VIAL_SD)
            size = DIET_MEANS[diet] + vial_effect + fly_noise

            day = first_day
            if rng.random() < 0.25:
                day = rng.choice(MEASUREMENT_DAYS)

            rows.append(
                {
                    "vial_id": vial_id,
                    "diet": diet,
                    "fly_id": "F{:02d}".format(fly_index),
                    "wing_centroid_size_mm": "{:.3f}".format(round(size, 3)),
                    "day_after_eclosion": day,
                }
            )

    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_CSV)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} ({} data rows)".format(out_path, len(rows)))


if __name__ == "__main__":
    main()
