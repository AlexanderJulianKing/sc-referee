"""Generate the wing-length dataset for the larval crowding experiment.

Rears 16 trays (8 low density, 8 high density) and records the right wing
length of 10 emerged adult females per tray. Standard library only.

Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260880

N_TRAYS_PER_TREATMENT = 8
N_MOSQUITOES_PER_TRAY = 10

MEAN_WING_MM = {"low": 2.98, "high": 2.79}
SD_BETWEEN_TRAYS_MM = 0.08
SD_WITHIN_TRAY_MM = 0.11

# Emergence is scored in days after the larval trays were seeded.
EMERGENCE_DAY_RANGE = {"low": (9, 11), "high": (10, 13)}

OUT_FILE = "wing_lengths.csv"
COLUMNS = [
    "tray.ref",
    "density.treatment",
    "emergence.day",
    "mosquito.no",
    "wing.length.mm",
]


def build_rows(rng):
    treatments = ["low"] * N_TRAYS_PER_TREATMENT + ["high"] * N_TRAYS_PER_TREATMENT
    rng.shuffle(treatments)

    rows = []
    for tray_index, treatment in enumerate(treatments, start=1):
        tray_ref = "TRAY-{:02d}".format(tray_index)
        tray_offset = rng.gauss(0.0, SD_BETWEEN_TRAYS_MM)
        tray_mean = MEAN_WING_MM[treatment] + tray_offset

        first_day, last_day = EMERGENCE_DAY_RANGE[treatment]
        tray_start_day = rng.randint(first_day, last_day - 1)

        for mosquito_no in range(1, N_MOSQUITOES_PER_TRAY + 1):
            wing = rng.gauss(tray_mean, SD_WITHIN_TRAY_MM)
            emergence_day = tray_start_day + rng.choice([0, 0, 1, 1, 2])
            rows.append(
                {
                    "tray.ref": tray_ref,
                    "density.treatment": treatment,
                    "emergence.day": emergence_day,
                    "mosquito.no": mosquito_no,
                    "wing.length.mm": "{:.2f}".format(round(wing, 2)),
                }
            )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_FILE)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
