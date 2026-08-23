"""Generate the single-unit threshold table for the rearing-condition study.

Fourteen gerbils (7 quiet-reared, 7 noise-reared), each contributing 9-16
well-isolated single units from primary auditory cortex.  One row = one unit.

Standard library only.  Fixed seed, so the CSV is reproducible.
"""

import csv
import os
import random

SEED = 20260885

# dB SPL at characteristic frequency
GROUP_MEAN = {"quiet": 24.0, "noise": 33.0}
BETWEEN_ANIMAL_SD = 3.0   # animal-to-animal spread of mean threshold
WITHIN_ANIMAL_SD = 6.0    # unit-to-unit scatter inside one animal

MIN_UNITS, MAX_UNITS = 9, 16

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unit_thresholds.csv")


def main():
    rng = random.Random(SEED)

    animals = []
    for i in range(1, 8):
        animals.append(("G%02d" % i, "quiet"))
    for i in range(8, 15):
        animals.append(("G%02d" % i, "noise"))

    rows = []
    for animal_id, condition in animals:
        animal_offset = rng.gauss(0.0, BETWEEN_ANIMAL_SD)
        n_units = rng.randint(MIN_UNITS, MAX_UNITS)
        for u in range(1, n_units + 1):
            thr = GROUP_MEAN[condition] + animal_offset + rng.gauss(0.0, WITHIN_ANIMAL_SD)
            # thresholds are read off rate-level functions to the nearest 0.1 dB
            # and cannot fall below the 0 dB SPL floor of the calibrated system
            thr = max(0.0, round(thr, 1))
            rows.append({
                "animal_id": animal_id,
                "rearing_condition": condition,
                "unit_id": "%s-u%02d" % (animal_id, u),
                "cf_threshold_db_spl": "%.1f" % thr,
            })

    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["animal_id", "rearing_condition", "unit_id", "cf_threshold_db_spl"],
        )
        w.writeheader()
        w.writerows(rows)

    print("wrote %s (%d rows)" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
