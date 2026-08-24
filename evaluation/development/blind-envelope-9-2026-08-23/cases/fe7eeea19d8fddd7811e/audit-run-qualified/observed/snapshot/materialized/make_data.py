"""Generate the home blood-pressure study dataset.

Twenty-four adults, twelve in a supervised walking programme and twelve given a
printed lifestyle leaflet, each measuring morning seated systolic blood pressure
at home on seven consecutive days.

Standard library only. Fixed seed so the CSV is reproducible byte for byte.
"""

import csv
import os
import random

# Fixed seed. This particular value was chosen so that the realised sample
# magnitudes land on the study description above: a walking-minus-leaflet gap of
# about 4.5 mmHg, within-person day-to-day SD near 5 mmHg, between-person SD
# near 9 mmHg, and readings mostly inside 124-150 mmHg.
SEED = 20262802

N_PER_GROUP = 12
N_DAYS = 7

# Group means for the underlying true participant level (mmHg).
LEAFLET_MEAN = 139.0
WALKING_MEAN = 134.4          # ~4.6 mmHg lower than leaflet

BETWEEN_PERSON_SD = 9.5       # spread between different adults
WITHIN_PERSON_SD = 5.0        # day-to-day variation inside one adult

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "home_bp_readings.csv")


def main():
    rng = random.Random(SEED)

    codes = ["PT%02d" % i for i in range(1, 2 * N_PER_GROUP + 1)]

    # Randomised allocation: twelve to each programme.
    allocation = ["walking"] * N_PER_GROUP + ["leaflet"] * N_PER_GROUP
    rng.shuffle(allocation)

    rows = []
    for code, programme in zip(codes, allocation):
        group_mean = WALKING_MEAN if programme == "walking" else LEAFLET_MEAN
        # This adult's own usual morning level.
        person_level = rng.gauss(group_mean, BETWEEN_PERSON_SD)
        for day in range(1, N_DAYS + 1):
            reading = person_level + rng.gauss(0.0, WITHIN_PERSON_SD)
            rows.append(
                {
                    "participant_code": code,
                    "programme": programme,
                    "day": day,
                    "systolic_bp_mmhg": int(round(reading)),
                }
            )

    fields = ["participant_code", "programme", "day", "systolic_bp_mmhg"]
    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
