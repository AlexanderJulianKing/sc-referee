"""Generate the harvest sampling table for the grow-out feed comparison.

Design: 10 sea cages stocked from one smolt batch, assigned whole to a feed
(5 cages standard high-fishmeal, 5 cages reformulated algal-oil). At harvest,
12 fish are netted at random from each cage and measured individually,
giving 120 measured fish.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260822
N_CAGES_PER_FEED = 5
N_FISH_PER_CAGE = 12

# Site prefix + pen number, the way pens are labelled on the farm manifest.
SITE = "HVR"

# Cage -> feed assignment. Pens alternate along the walkway, so the two feeds
# are interleaved rather than blocked into the first and last five pens.
CAGE_PLAN = [
    ("HVR-P01", "standard"),
    ("HVR-P02", "algal_oil"),
    ("HVR-P04", "standard"),
    ("HVR-P05", "algal_oil"),
    ("HVR-P07", "standard"),
    ("HVR-P08", "algal_oil"),
    ("HVR-P09", "standard"),
    ("HVR-P11", "algal_oil"),
    ("HVR-P12", "standard"),
    ("HVR-P14", "algal_oil"),
]

# Fillet omega-3 (mg EPA+DHA per g wet fillet) model, on the mg/g scale:
#   value = feed mean + cage offset + weight slope * (weight - 5.25) + fish noise
FEED_MEAN = {"standard": 10.95, "algal_oil": 13.45}
CAGE_SD = 0.55          # drift between cages on the same feed
FISH_SD = 1.05          # spread among fish within one cage
WEIGHT_SLOPE = 0.55     # heavier fish carry slightly fatter fillets

# Harvest weight (kg) model.
WEIGHT_MEAN = 5.20
WEIGHT_CAGE_SD = 0.18
WEIGHT_FISH_SD = 0.42
WEIGHT_MIN, WEIGHT_MAX = 4.0, 6.5

OMEGA3_MIN, OMEGA3_MAX = 7.5, 18.0

OUT_NAME = "harvest_fillet_omega3.csv"
HEADER = ["cage_id", "feed", "fish_number", "harvest_weight_kg", "omega3_mg_per_g"]


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)
    rows = []

    for cage_id, feed in CAGE_PLAN:
        cage_offset = rng.gauss(0.0, CAGE_SD)
        cage_weight_offset = rng.gauss(0.0, WEIGHT_CAGE_SD)

        for fish_number in range(1, N_FISH_PER_CAGE + 1):
            weight = clamp(
                rng.gauss(WEIGHT_MEAN + cage_weight_offset, WEIGHT_FISH_SD),
                WEIGHT_MIN,
                WEIGHT_MAX,
            )
            omega3 = (
                FEED_MEAN[feed]
                + cage_offset
                + WEIGHT_SLOPE * (weight - WEIGHT_MEAN)
                + rng.gauss(0.0, FISH_SD)
            )
            omega3 = clamp(omega3, OMEGA3_MIN, OMEGA3_MAX)

            rows.append(
                [
                    cage_id,
                    feed,
                    fish_number,
                    "%.2f" % round(weight, 2),
                    "%.2f" % round(omega3, 2),
                ]
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
