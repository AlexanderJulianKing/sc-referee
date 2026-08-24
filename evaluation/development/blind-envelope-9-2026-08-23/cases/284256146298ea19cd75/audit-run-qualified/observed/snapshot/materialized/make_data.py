"""Generate the farm pond smooth newt survey table.

Fifteen working-farm ponds were surveyed. Eight are ringed by a fenced grass
buffer strip; seven allow livestock access to the water's edge. Five adult male
smooth newts were bottle-trapped and weighed in each pond, so the table holds
75 weighed animals.

Each pond gets its own average body mass, and the five newts caught in that pond
are drawn around that pond average. Newts from the same pond therefore resemble
each other more closely than newts from different ponds, as real survey data of
this kind do. Draws falling outside the plausible mass range for an adult male
smooth newt are redrawn rather than clipped, so no mass piles up at the limits.

Standard library only. The seed is fixed, so re-running reproduces the file
byte for byte.
"""

import csv
import os
import random

SEED = 17697

# Pond-level design: pond code -> buffer strip status.
# Eight fenced buffer strips, seven with livestock access to the water's edge.
PONDS = [
    ("PND-01", "buffered"),
    ("PND-02", "unfenced"),
    ("PND-03", "buffered"),
    ("PND-04", "buffered"),
    ("PND-05", "unfenced"),
    ("PND-06", "unfenced"),
    ("PND-07", "buffered"),
    ("PND-08", "buffered"),
    ("PND-09", "unfenced"),
    ("PND-10", "buffered"),
    ("PND-11", "unfenced"),
    ("PND-12", "unfenced"),
    ("PND-13", "buffered"),
    ("PND-14", "buffered"),
    ("PND-15", "unfenced"),
]

NEWTS_PER_POND = 5

# All masses in grams.
UNFENCED_MEAN_G = 2.75   # average newt in a pond with livestock access
BUFFER_EFFECT_G = 0.50   # extra mass in a pond with a fenced buffer strip
POND_SD_G = 0.55         # spread between pond averages
NEWT_SD_G = 0.50         # spread between newts caught in the same pond
MASS_MIN_G = 1.60        # plausible range for an adult male smooth newt
MASS_MAX_G = 4.40
SCALE_RESOLUTION_G = 0.01  # the field balance reads to the centigram

FIELDNAMES = ["pond_code", "buffer_strip", "newt_number", "body_mass_g"]
OUTPUT_NAME = "newt_body_mass.csv"


def main():
    rng = random.Random(SEED)
    rows = []

    for pond_code, buffer_strip in PONDS:
        pond_mean = UNFENCED_MEAN_G + rng.gauss(0.0, POND_SD_G)
        if buffer_strip == "buffered":
            pond_mean += BUFFER_EFFECT_G

        for newt_number in range(1, NEWTS_PER_POND + 1):
            while True:
                mass = pond_mean + rng.gauss(0.0, NEWT_SD_G)
                if MASS_MIN_G <= mass <= MASS_MAX_G:
                    break
            mass = round(mass / SCALE_RESOLUTION_G) * SCALE_RESOLUTION_G
            rows.append(
                {
                    "pond_code": pond_code,
                    "buffer_strip": buffer_strip,
                    "newt_number": newt_number,
                    "body_mass_g": "%.2f" % mass,
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
