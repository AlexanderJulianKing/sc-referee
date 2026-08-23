"""Generate the sourdough starter pH bench table.

Twelve starter jars (six fed wholemeal rye, six fed refined white wheat) are
read once a day for six days of maturation, giving 12 x 6 = 72 rows.

Standard library only. Fixed seed, so the CSV is reproducible.
"""

import csv
import math
import os
import random

SEED = 20260823
N_JARS_PER_FLOUR = 6
DAYS = range(1, 7)

START_PH = 5.60          # both flours start near this on day 1
PLATEAU = {              # pH each flour settles toward by day 6
    "wholemeal_rye": 3.60,
    "refined_white_wheat": 3.90,
}
DECAY = 0.90             # acidification rate constant (per day)
JAR_SD = 0.12            # jar-to-jar offset, pH units
NOISE_SD = 0.08          # day-to-day measurement scatter within a jar, pH units

PH_MIN, PH_MAX = 3.30, 5.80

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "starter_ph_readings.csv")


def mean_ph(flour, day):
    """Exponential approach from the day-1 start pH down to the flour plateau."""
    plateau = PLATEAU[flour]
    return plateau + (START_PH - plateau) * math.exp(-DECAY * (day - 1))


def main():
    rng = random.Random(SEED)

    jars = []
    jar_number = 0
    for flour in ("wholemeal_rye", "refined_white_wheat"):
        for _ in range(N_JARS_PER_FLOUR):
            jar_number += 1
            jars.append(("jar_%02d" % jar_number, flour, rng.gauss(0.0, JAR_SD)))

    rows = []
    for jar_id, flour, jar_offset in jars:
        for day in DAYS:
            value = mean_ph(flour, day) + jar_offset + rng.gauss(0.0, NOISE_SD)
            value = min(max(value, PH_MIN), PH_MAX)
            rows.append(
                {
                    "jar_id": jar_id,
                    "flour_type": flour,
                    "maturation_day": day,
                    "starter_ph": "%.2f" % value,
                }
            )

    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["jar_id", "flour_type", "maturation_day", "starter_ph"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
