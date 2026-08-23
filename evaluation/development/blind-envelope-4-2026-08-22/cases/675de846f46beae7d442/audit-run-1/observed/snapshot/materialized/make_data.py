"""Generate the harbour seal pup weekly weighing dataset.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design
------
20 orphaned harbour seal pups (HS-101 .. HS-120), 10 on the centre's standard
diet and 10 on the high-fat fish-oil supplemented diet. Each pup is weighed
once a week for 8 consecutive weeks in care, giving 20 * 8 = 160 weighing rows.

Model
-----
    body_mass_kg = admission_mass + weekly_gain[diet] * (week_in_care - 1) + noise

  admission_mass ~ Normal(18.4, 2.0)   pup-level mass at the week 1 weighing
  weekly_gain    = 1.3 kg/week (standard), 1.7 kg/week (supplemented)
  noise          ~ Normal(0, 0.4)      scale reading and gut fill

Masses are rounded to one decimal place, floored at 13.0 kg, and forced to be
non-decreasing within a pup so no animal appears to lose mass.
"""

import csv
import os
import random

SEED = 2
N_PUPS_PER_GROUP = 10
N_WEEKS = 8

ADMISSION_MEAN = 18.4
ADMISSION_SD = 2.0
WEEKLY_GAIN = {"standard": 1.3, "supplemented": 1.7}
WEIGHING_NOISE_SD = 0.4
MIN_MASS_KG = 13.0

OUT_NAME = "seal_pup_masses.csv"


def build_rows(rng):
    rows = []
    tag_number = 101
    for group in ("standard", "supplemented"):
        for _ in range(N_PUPS_PER_GROUP):
            tag = "HS-%d" % tag_number
            tag_number += 1
            admission = rng.gauss(ADMISSION_MEAN, ADMISSION_SD)
            previous = None
            for week in range(1, N_WEEKS + 1):
                mass = admission + WEEKLY_GAIN[group] * (week - 1)
                mass += rng.gauss(0.0, WEIGHING_NOISE_SD)
                mass = max(mass, MIN_MASS_KG)
                if previous is not None and mass < previous:
                    mass = previous
                mass = round(mass, 1)
                previous = mass
                rows.append([tag, group, week, "%.1f" % mass])
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pup_tag", "diet_group", "week_in_care", "body_mass_kg"])
        writer.writerows(rows)
    print("wrote %d data rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
