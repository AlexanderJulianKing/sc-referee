"""Simulate the wall lizard morphometrics dataset.

Field design: 44 adult male wall lizards were captured, measured, marked and
released across two small offshore islands, 22 per island. Each animal was
captured once and measured once, so one row of the CSV is one individual.

Standard library only. Fixed seed so the CSV is reproducible.
"""

import csv
import os
import random

SEED = 20260822

# One site per predator community.
SITES = [
    ("Isola Corvo", "snakes_present", 68.0, 5.0),
    ("Isola Rossa", "snakes_absent", 74.0, 5.0),
]

N_PER_ISLAND = 22
SVL_MIN = 55.0   # believable adult lower bound (mm)
SVL_MAX = 88.0   # believable adult upper bound (mm)


def draw_svl(rng, mean, sd):
    """Draw one snout-to-vent length, redrawing until it is a believable adult."""
    while True:
        value = rng.gauss(mean, sd)
        if SVL_MIN <= value <= SVL_MAX:
            return round(value, 1)


def main():
    rng = random.Random(SEED)

    lizards = []
    for island, predator_status, mean, sd in SITES:
        for _ in range(N_PER_ISLAND):
            lizards.append(
                {
                    "island": island,
                    "predator_status": predator_status,
                    "svl_mm": draw_svl(rng, mean, sd),
                }
            )

    # Capture order mixes the two islands; ids are assigned in capture order.
    rng.shuffle(lizards)
    for i, lizard in enumerate(lizards, start=1):
        lizard["lizard_id"] = "L%03d" % i

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lizard_svl.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["lizard_id", "island", "predator_status", "svl_mm"]
        )
        writer.writeheader()
        writer.writerows(lizards)

    print("wrote %s (%d data rows)" % (out_path, len(lizards)))


if __name__ == "__main__":
    main()
