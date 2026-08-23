"""Generate the seagrass exclusion-zone survey dataset.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design: 12 meadows (6 protected, 6 open to mooring), 8 haphazardly placed dive
points per meadow, one shoot measured per point => 96 rows.
"""

import csv
import os
import random

SEED = 20260040

N_MEADOWS_PER_ZONE = 6
N_POINTS_PER_MEADOW = 8

# Zone-level centres for maximum leaf length (cm).
ZONE_MEAN_CM = {"open": 48.0, "protected": 63.0}
# Meadow-to-meadow spread around the zone centre (cm).
BETWEEN_MEADOW_SD_CM = 7.0
# Point-to-point spread inside one meadow (cm).
WITHIN_MEADOW_SD_CM = 9.0

LEAF_MIN_CM, LEAF_MAX_CM = 25.0, 95.0
DEPTH_MIN_M, DEPTH_MAX_M = 1.5, 6.0

SEDIMENT_TYPES = ["fine_sand", "medium_sand", "muddy_sand", "silt", "shell_gravel"]

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seagrass_survey.csv")


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Meadows MDW01..MDW06 sit inside the exclusion zone (protected);
    # MDW07..MDW12 sit in adjacent water open to mooring.
    meadows = []
    for i in range(1, N_MEADOWS_PER_ZONE * 2 + 1):
        zone = "protected" if i <= N_MEADOWS_PER_ZONE else "open"
        meadow_mean = rng.gauss(ZONE_MEAN_CM[zone], BETWEEN_MEADOW_SD_CM)
        # Each meadow has its own depth band and its own sediment mix.
        depth_centre = rng.uniform(2.2, 5.2)
        weights = [rng.uniform(0.2, 1.0) for _ in SEDIMENT_TYPES]
        meadows.append(
            {
                "meadow_id": "MDW%02d" % i,
                "zone": zone,
                "mean_cm": meadow_mean,
                "depth_centre_m": depth_centre,
                "sediment_weights": weights,
            }
        )

    rows = []
    for meadow in meadows:
        for point in range(1, N_POINTS_PER_MEADOW + 1):
            leaf = rng.gauss(meadow["mean_cm"], WITHIN_MEADOW_SD_CM)
            leaf = clamp(leaf, LEAF_MIN_CM, LEAF_MAX_CM)

            depth = clamp(
                rng.gauss(meadow["depth_centre_m"], 0.55), DEPTH_MIN_M, DEPTH_MAX_M
            )

            sediment = rng.choices(SEDIMENT_TYPES, weights=meadow["sediment_weights"])[0]

            rows.append(
                {
                    "meadow_id": meadow["meadow_id"],
                    "zone": meadow["zone"],
                    "point_number": point,
                    "leaf_length_cm": round(leaf, 1),
                    "depth_m": round(depth, 2),
                    "sediment_type": sediment,
                }
            )

    fieldnames = [
        "meadow_id",
        "zone",
        "point_number",
        "leaf_length_cm",
        "depth_m",
        "sediment_type",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_PATH, len(rows)))


if __name__ == "__main__":
    main()
