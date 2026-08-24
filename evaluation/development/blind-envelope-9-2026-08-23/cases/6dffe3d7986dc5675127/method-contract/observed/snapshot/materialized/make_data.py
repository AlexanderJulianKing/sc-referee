"""Generate the hedgehog overwintering dataset.

Study design: 40 adult West European hedgehogs (Erinaceus europaeus), 20 tracked in
suburban gardens and 20 on rural farmland, through a single winter. Each animal was
weighed once shortly before entering hibernation and once shortly after emergence, and
that pair of weights was reduced to a single percentage mass change for the animal.

Each hedgehog therefore contributes exactly one row. There are no repeated measurements
on the same animal in the delivered table, so the animal and the row are the same unit.

Standard library only. Fixed seed, so the CSV is reproducible byte-for-byte.
"""

import csv
import os
import random

SEED = 20260823
N_PER_GROUP = 20
N_TOTAL = 2 * N_PER_GROUP

# Mean percentage-point loss by landscape. Suburban garden animals lose about
# 5 percentage points less than rural farmland animals (supplemental garden food,
# milder microclimate). Within-landscape spread is about 4 percentage points.
GROUP_MEAN_LOSS = {"suburban_garden": 19.0, "rural_farmland": 24.0}
GROUP_SD_LOSS = 4.6

# Pre-hibernation mass in grams, by landscape. Suburban animals go into hibernation
# a little heavier.
GROUP_MEAN_MASS_G = {"suburban_garden": 1010.0, "rural_farmland": 930.0}
GROUP_SD_MASS_G = 115.0

# Heavier animals draw down a slightly smaller fraction of their body mass. Expressed
# as percentage points of loss per gram of pre-hibernation mass above the group mean.
MASS_SLOPE_PP_PER_G = -0.006

MASS_MIN_G, MASS_MAX_G = 700, 1300
LOSS_MIN_PCT, LOSS_MAX_PCT = 6.0, 36.0

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "hedgehog_overwinter_mass.csv")


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Tag codes HH-01 .. HH-40. Landscape is assigned at random, 20 animals each, so
    # tag order does not encode group.
    ids = ["HH-%02d" % i for i in range(1, N_TOTAL + 1)]
    landscapes = ["suburban_garden"] * N_PER_GROUP + ["rural_farmland"] * N_PER_GROUP
    rng.shuffle(landscapes)

    rows = []
    for hedgehog_id, landscape in zip(ids, landscapes):
        mean_mass = GROUP_MEAN_MASS_G[landscape]
        mass_g = clamp(
            rng.gauss(mean_mass, GROUP_SD_MASS_G), MASS_MIN_G, MASS_MAX_G
        )

        # Percentage points of mass lost over hibernation, always positive here.
        loss_pct = rng.gauss(GROUP_MEAN_LOSS[landscape], GROUP_SD_LOSS)
        loss_pct += MASS_SLOPE_PP_PER_G * (mass_g - mean_mass)
        # Scale reading and handling noise on the two weighings.
        loss_pct += rng.gauss(0.0, 0.45)
        loss_pct = clamp(loss_pct, LOSS_MIN_PCT, LOSS_MAX_PCT)

        rows.append(
            {
                "hedgehog_id": hedgehog_id,
                "landscape": landscape,
                "pre_hibernation_mass_g": int(round(mass_g)),
                # Reported as a signed change, so a loss is negative.
                "mass_change_percent": round(-loss_pct, 1),
            }
        )

    fieldnames = [
        "hedgehog_id",
        "landscape",
        "pre_hibernation_mass_g",
        "mass_change_percent",
    ]
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
