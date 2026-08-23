"""Generate the snail-level dataset for the dietary calcium enclosure study.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design: 14 outdoor mesh enclosures, 7 on standard feed and 7 on feed with added
calcium carbonate. Each enclosure contributes 20 individually weighed snails.

Weight model (grams):
    live_weight = group_mean + enclosure_effect + snail_noise
        group_mean        = 9.4 (standard) or 11.2 (added calcium)
        enclosure_effect  ~ Normal(0, 1.1)   between-enclosure variation
        snail_noise       ~ Normal(0, 1.6)   between-snail variation inside an enclosure

Shell diameter (mm) tracks weight:
    shell_diameter = 32.0 + 1.0 * (live_weight - 10.3) + Normal(0, 0.9)
    then clipped to the plausible measurable range [26.0, 38.0].
"""

import csv
import os
import random

SEED = 20260822

N_ENCLOSURES_PER_GROUP = 7
N_SNAILS_PER_ENCLOSURE = 20

GROUP_MEAN_G = {"standard": 9.4, "added_calcium": 11.2}
SD_BETWEEN_ENCLOSURES_G = 1.1
SD_WITHIN_ENCLOSURE_G = 1.6

DIAMETER_INTERCEPT_MM = 32.0
DIAMETER_SLOPE_MM_PER_G = 1.0
DIAMETER_CENTRE_G = 10.3
SD_DIAMETER_NOISE_MM = 0.9
DIAMETER_MIN_MM = 26.0
DIAMETER_MAX_MM = 38.0

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(OUT_DIR, "snail_weights.csv")

COLUMNS = [
    "enclosure_ref",
    "calcium_level",
    "snail_no",
    "live_weight_g",
    "shell_diameter_mm",
]


def build_rows(rng):
    rows = []
    enclosure_index = 0
    # Alternate the two feed groups across enclosure numbering, as the farm
    # assigned feed to enclosures in alternating order along the row of pens.
    assignments = []
    for i in range(N_ENCLOSURES_PER_GROUP):
        assignments.append("standard")
        assignments.append("added_calcium")

    for calcium_level in assignments:
        enclosure_index += 1
        enclosure_ref = "ENC-{:02d}".format(enclosure_index)
        enclosure_effect = rng.gauss(0.0, SD_BETWEEN_ENCLOSURES_G)
        base = GROUP_MEAN_G[calcium_level] + enclosure_effect

        for snail_no in range(1, N_SNAILS_PER_ENCLOSURE + 1):
            weight = base + rng.gauss(0.0, SD_WITHIN_ENCLOSURE_G)
            # Snails collected for weighing are growing animals; guard against
            # an implausible non-positive draw in the tail.
            if weight < 3.0:
                weight = 3.0

            diameter = (
                DIAMETER_INTERCEPT_MM
                + DIAMETER_SLOPE_MM_PER_G * (weight - DIAMETER_CENTRE_G)
                + rng.gauss(0.0, SD_DIAMETER_NOISE_MM)
            )
            if diameter < DIAMETER_MIN_MM:
                diameter = DIAMETER_MIN_MM
            if diameter > DIAMETER_MAX_MM:
                diameter = DIAMETER_MAX_MM

            rows.append(
                {
                    "enclosure_ref": enclosure_ref,
                    "calcium_level": calcium_level,
                    "snail_no": snail_no,
                    "live_weight_g": round(weight, 2),
                    "shell_diameter_mm": round(diameter, 1),
                }
            )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} data rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
