"""Generate the on-farm sugar beet seed treatment dataset.

One row per commercial field. Thirty-four fields, each on a different farm,
seventeen drilled with standard fungicide-treated seed and seventeen with seed
carrying an added biological coating. Each field was harvested whole and the
delivered clean root yield was taken once from the weighbridge tickets.

Standard library only. Fixed seed so the CSV is reproducible.
"""

import csv
import random

SEED = 20261037
N_PER_GROUP = 17

# Yield model, tonnes per hectare of clean root.
MEAN_STANDARD = 62.0
MEAN_BIOLOGICAL = 67.0
SD_FIELD = 7.0
YIELD_MIN = 44.0
YIELD_MAX = 86.0

# Field area, hectares.
AREA_MEAN = 14.0
AREA_SD = 4.5
AREA_MIN = 5.2
AREA_MAX = 27.0

OUT_PATH = "sugar_beet_field_yields.csv"


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Field identifiers: one per farm, in the regional trial numbering.
    numbers = list(range(101, 101 + 2 * N_PER_GROUP))
    rng.shuffle(numbers)

    treatments = ["standard"] * N_PER_GROUP + ["biological"] * N_PER_GROUP
    rng.shuffle(treatments)

    rows = []
    for number, treatment in zip(sorted(numbers), treatments):
        mean = MEAN_BIOLOGICAL if treatment == "biological" else MEAN_STANDARD
        yield_t_ha = clamp(rng.gauss(mean, SD_FIELD), YIELD_MIN, YIELD_MAX)
        area_ha = clamp(rng.gauss(AREA_MEAN, AREA_SD), AREA_MIN, AREA_MAX)
        rows.append(
            {
                "field_id": "SB-{:03d}".format(number),
                "seed_treatment": treatment,
                "field_area_ha": "{:.1f}".format(area_ha),
                "clean_root_yield_t_ha": "{:.1f}".format(yield_t_ha),
            }
        )

    fieldnames = [
        "field_id",
        "seed_treatment",
        "field_area_ha",
        "clean_root_yield_t_ha",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
