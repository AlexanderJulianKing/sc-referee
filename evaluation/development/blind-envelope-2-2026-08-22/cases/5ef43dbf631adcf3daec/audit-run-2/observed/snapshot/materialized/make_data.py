"""Generate the greenhouse tomato mycorrhiza trial data set.

One potted plant is the experimental unit. 48 plants, 24 inoculated and 24
uninoculated controls, each harvested once, one row per plant.

Run with: python3 make_data.py
Writes: greenhouse_tomato_yield.csv (48 data rows + header)

Standard library only, fixed seed, so the file is reproducible byte for byte.
"""

import csv
import os
import random

SEED = 20260822
N_PER_GROUP = 24
N_PLANTS = 2 * N_PER_GROUP

# Yield model (cumulative marketable fresh fruit mass per plant, grams).
YIELD_MEAN = {"control": 1820.0, "inoculated": 2260.0}
YIELD_SD = 330.0

# Plant height at first flower (cm).
HEIGHT_MEAN = {"control": 61.0, "inoculated": 65.0}
HEIGHT_SD = 6.0

# Mean fresh mass of a single marketable fruit (g), used to turn a plant's
# total yield into a plausible fruit count.
FRUIT_MASS_MEAN = 118.0
FRUIT_MASS_SD = 12.0

N_BENCHES = 4
SLOTS_PER_BENCH = 12

OUT_NAME = "greenhouse_tomato_yield.csv"


def main() -> None:
    rng = random.Random(SEED)

    # Randomise treatment assignment over the 48 plants.
    treatments = ["inoculated"] * N_PER_GROUP + ["control"] * N_PER_GROUP
    rng.shuffle(treatments)

    # Randomise final bench position: every plant gets its own slot.
    slots = [
        "B{}-{:02d}".format(bench, slot)
        for bench in range(1, N_BENCHES + 1)
        for slot in range(1, SLOTS_PER_BENCH + 1)
    ]
    assert len(slots) == N_PLANTS
    rng.shuffle(slots)

    rows = []
    for i in range(N_PLANTS):
        plant_id = "P{:02d}".format(i + 1)
        treatment = treatments[i]

        yield_g = rng.gauss(YIELD_MEAN[treatment], YIELD_SD)
        yield_g = max(yield_g, 250.0)  # a harvested plant still yields something

        height_cm = rng.gauss(HEIGHT_MEAN[treatment], HEIGHT_SD)

        fruit_mass = max(rng.gauss(FRUIT_MASS_MEAN, FRUIT_MASS_SD), 70.0)
        fruit_count = max(int(round(yield_g / fruit_mass)), 1)

        rows.append(
            {
                "plant_id": plant_id,
                "treatment": treatment,
                "bench_position": slots[i],
                "height_cm_at_first_flower": round(height_cm, 1),
                "marketable_fruit_count": fruit_count,
                "marketable_yield_g": int(round(yield_g)),
            }
        )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fieldnames = [
        "plant_id",
        "treatment",
        "bench_position",
        "height_cm_at_first_flower",
        "marketable_fruit_count",
        "marketable_yield_g",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
