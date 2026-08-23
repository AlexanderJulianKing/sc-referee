"""Generate the berry-level data file for the strawberry deficit-irrigation trial.

Twenty-four mother plants (12 deficit, 12 full irrigation) grown in a polytunnel with
four rows of six plants. Six ripe berries were picked from each plant at harvest, so
the generated table holds 24 * 6 = 144 berry rows.

Values are invented but are drawn from a plausible nested structure: each plant gets its
own offset, and each berry varies around its own plant's level.

Run with a fixed seed so the file is reproducible:
    /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822

N_PLANTS_PER_GROUP = 12
N_BERRIES_PER_PLANT = 6
PLANTS_PER_ROW = 6

# Soluble solids (degrees Brix)
BRIX_MEAN = {"deficit": 8.6, "full": 7.5}
BRIX_SD_PLANT = 0.6     # spread between mother plants
BRIX_SD_BERRY = 0.9     # berry-to-berry spread within one plant

# Berry fresh weight (grams). Deficit irrigation gives somewhat smaller berries,
# so the two schedule means straddle the target average of about 18 g.
WEIGHT_MEAN = {"deficit": 17.2, "full": 18.8}
WEIGHT_SD_PLANT = 1.2
WEIGHT_SD_BERRY = 2.0

# Plausibility limits for a ripe strawberry measured on a hand refractometer and a bench
# balance. Draws falling outside these limits are redrawn rather than clipped, so no values
# pile up on the boundary. Both limits sit more than two standard deviations from their
# group means, so redrawing is rare and leaves the target spreads essentially intact.
BRIX_LIMITS = (5.0, 13.0)
WEIGHT_LIMITS = (6.0, 35.0)

OUT_NAME = "strawberry_brix.csv"
FIELDNAMES = [
    "plant_id",
    "irrigation_schedule",
    "berry_id",
    "soluble_solids_brix",
    "berry_fresh_weight_g",
    "polytunnel_row",
]


def bounded_gauss(mean, sd, limits):
    """Draw a Normal value, redrawing until it falls inside the plausibility limits."""
    low, high = limits
    while True:
        value = random.gauss(mean, sd)
        if low <= value <= high:
            return value


def assign_plants():
    """Lay 24 plants out over four polytunnel rows, three of each schedule per row.

    Returns a list of (plant_id, irrigation_schedule, polytunnel_row) in plant order.
    """
    schedules = ["deficit"] * N_PLANTS_PER_GROUP + ["full"] * N_PLANTS_PER_GROUP
    random.shuffle(schedules)

    # Re-balance so every polytunnel row carries three deficit and three full plants;
    # this keeps schedule from being confounded with row position.
    balanced = []
    n_rows = (2 * N_PLANTS_PER_GROUP) // PLANTS_PER_ROW
    per_row = [["deficit"] * (PLANTS_PER_ROW // 2) + ["full"] * (PLANTS_PER_ROW // 2)
               for _ in range(n_rows)]
    for row_block in per_row:
        random.shuffle(row_block)
        balanced.extend(row_block)

    plants = []
    for index, schedule in enumerate(balanced):
        plant_id = "P{:02d}".format(index + 1)
        polytunnel_row = index // PLANTS_PER_ROW + 1
        plants.append((plant_id, schedule, polytunnel_row))
    return plants


def main():
    random.seed(SEED)
    plants = assign_plants()

    rows = []
    for plant_id, schedule, polytunnel_row in plants:
        # One offset per mother plant, shared by all six of its berries.
        plant_brix_offset = random.gauss(0.0, BRIX_SD_PLANT)
        plant_weight_offset = random.gauss(0.0, WEIGHT_SD_PLANT)

        for berry_index in range(1, N_BERRIES_PER_PLANT + 1):
            brix = bounded_gauss(
                BRIX_MEAN[schedule] + plant_brix_offset, BRIX_SD_BERRY, BRIX_LIMITS)
            weight = bounded_gauss(
                WEIGHT_MEAN[schedule] + plant_weight_offset, WEIGHT_SD_BERRY, WEIGHT_LIMITS)
            # A hand refractometer reads to 0.1 Brix; the bench balance reads to 0.1 g.
            rows.append({
                "plant_id": plant_id,
                "irrigation_schedule": schedule,
                "berry_id": "{}_B{}".format(plant_id, berry_index),
                "soluble_solids_brix": "{:.1f}".format(round(brix, 1)),
                "berry_fresh_weight_g": "{:.1f}".format(round(weight, 1)),
                "polytunnel_row": polytunnel_row,
            })

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
