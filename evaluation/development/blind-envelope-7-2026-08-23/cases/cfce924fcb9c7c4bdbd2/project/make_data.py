"""Generate the raw sector-level RNFL thickness table for the glaucoma drop study.

Standard library only. Fixed seed so the CSV is reproducible.
Run:  python3 make_data.py
Writes rnfl_sector_thickness.csv next to this file.

Design encoded here:
  24 patients, 12 per drop regimen, 6 clock-hour sectors per study eye = 144 rows.
  thickness = regimen mean + patient offset + sector offset + measurement noise
"""

import csv
import os
import random

SEED = 20260823

# Regimen labels and their target mean RNFL thickness (micrometres).
REGIMENS = {
    "timolol": 78.0,      # older topical pressure-lowering regimen
    "latanoprost": 84.0,  # newer topical pressure-lowering regimen
}

# Six clock-hour sectors of the peripapillary scan, in clockwise reporting order.
# Offsets are anatomical: superior and inferior arcuate bundles are thick,
# nasal and temporal sectors are thin. The six offsets sum to zero, so they
# do not shift the regimen means. Their spread is about 11 um, and the
# measurement noise adds ~3 um, for roughly 12 um of within-eye variation.
SECTOR_OFFSETS = {
    "temporal": -15.5,
    "superotemporal": 11.0,
    "superonasal": 1.5,
    "nasal": -14.0,
    "inferonasal": 3.0,
    "inferotemporal": 14.0,
}

PATIENT_SD = 8.0   # between-patient variation
NOISE_SD = 3.0     # OCT measurement noise, per sector
N_PER_ARM = 12
FLOOR, CEILING = 45.0, 130.0

OUT_NAME = "rnfl_sector_thickness.csv"


def main():
    rng = random.Random(SEED)

    # Randomise which patients received which regimen, 12 per arm.
    patients = ["pt_%02d" % i for i in range(1, 2 * N_PER_ARM + 1)]
    arms = ["timolol"] * N_PER_ARM + ["latanoprost"] * N_PER_ARM
    rng.shuffle(arms)
    assignment = dict(zip(patients, arms))

    rows = []
    for patient_id in patients:
        regimen = assignment[patient_id]
        patient_offset = rng.gauss(0.0, PATIENT_SD)
        for sector, sector_offset in SECTOR_OFFSETS.items():
            value = (
                REGIMENS[regimen]
                + patient_offset
                + sector_offset
                + rng.gauss(0.0, NOISE_SD)
            )
            value = min(CEILING, max(FLOOR, value))
            rows.append(
                {
                    "patient_id": patient_id,
                    "drop_regimen": regimen,
                    "clock_hour_sector": sector,
                    "rnfl_thickness_um": round(value, 1),
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "patient_id",
                "drop_regimen",
                "clock_hour_sector",
                "rnfl_thickness_um",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
