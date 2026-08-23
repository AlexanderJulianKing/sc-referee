"""Generate the oyster-mushroom substrate trial dataset.

Fourteen growing chambers (seven supplemented, seven standard) are each
followed for four consecutive weekly flushes, giving one row per
chamber-flush and 56 rows in total.

Structure of the simulated values:
  * each chamber gets its own productivity offset, so chambers differ from
    one another in overall yield;
  * yield declines across successive flushes, the first flush being largest;
  * supplemented chambers are centred near 1400 g per flush and standard
    chambers near 1150 g per flush.

Values that must stay inside a stated range are drawn by rejection sampling
rather than clipped, so no value piles up exactly on a range boundary.

Standard library only. Fixed seed, so re-running reproduces the file exactly.
Run: /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260889
N_CHAMBERS = 14
N_FLUSHES = 4

# Group means for flush yield in grams, averaged over the four flushes.
GROUP_MEAN_G = {"standard": 1150.0, "supplemented": 1400.0}

# Offset added to the group mean for each successive flush (grams).
FLUSH_OFFSET_G = {1: 265.0, 2: 65.0, 3: -105.0, 4: -225.0}

# Chamber-to-chamber productivity spread and within-chamber flush noise.
CHAMBER_SD_G = 85.0
RESIDUAL_SD_G = 62.0
YIELD_MIN_G, YIELD_MAX_G = 700.0, 1900.0

# Chamber air temperature, degrees Celsius.
CHAMBER_TEMP_MEAN_C = 21.0
CHAMBER_TEMP_SD_C = 0.9
FLUSH_TEMP_SD_C = 0.5
TEMP_MIN_C, TEMP_MAX_C = 18.0, 24.0

# Days from spawning to the first flush, then the gap between flushes.
FIRST_FLUSH_DAY_MEAN = 21.0
FIRST_FLUSH_DAY_SD = 1.5
FIRST_FLUSH_DAY_MIN, FIRST_FLUSH_DAY_MAX = 18.0, 25.0
FLUSH_GAP_DAYS_MEAN = 7.6
FLUSH_GAP_DAYS_SD = 0.9
FLUSH_GAP_DAYS_MIN, FLUSH_GAP_DAYS_MAX = 6.0, 10.0

MAX_DRAWS = 200

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flush_yields.csv")

FIELDNAMES = [
    "chamber_id",
    "substrate",
    "flush_number",
    "flush_yield_g",
    "air_temp_c",
    "days_from_spawn",
]


def bounded_gauss(rng, mean, sd, low, high):
    """Normal draw restricted to [low, high] by rejection sampling."""
    for _ in range(MAX_DRAWS):
        value = rng.gauss(mean, sd)
        if low <= value <= high:
            return value
    raise RuntimeError(
        "no draw in [{}, {}] after {} attempts".format(low, high, MAX_DRAWS)
    )


def main():
    rng = random.Random(SEED)

    # Substrates alternate down the chamber list so neither group is one
    # contiguous block of identifiers.
    substrates = [
        "supplemented" if i % 2 == 0 else "standard" for i in range(N_CHAMBERS)
    ]

    rows = []
    for index, substrate in enumerate(substrates):
        chamber_id = "CH{:02d}".format(index + 1)
        chamber_effect_g = rng.gauss(0.0, CHAMBER_SD_G)
        chamber_temp_c = bounded_gauss(
            rng,
            CHAMBER_TEMP_MEAN_C,
            CHAMBER_TEMP_SD_C,
            TEMP_MIN_C + 0.6,
            TEMP_MAX_C - 0.6,
        )
        day = bounded_gauss(
            rng,
            FIRST_FLUSH_DAY_MEAN,
            FIRST_FLUSH_DAY_SD,
            FIRST_FLUSH_DAY_MIN,
            FIRST_FLUSH_DAY_MAX,
        )

        for flush_number in range(1, N_FLUSHES + 1):
            if flush_number > 1:
                day += bounded_gauss(
                    rng,
                    FLUSH_GAP_DAYS_MEAN,
                    FLUSH_GAP_DAYS_SD,
                    FLUSH_GAP_DAYS_MIN,
                    FLUSH_GAP_DAYS_MAX,
                )

            centre_g = (
                GROUP_MEAN_G[substrate]
                + FLUSH_OFFSET_G[flush_number]
                + chamber_effect_g
            )
            yield_g = bounded_gauss(
                rng, centre_g, RESIDUAL_SD_G, YIELD_MIN_G, YIELD_MAX_G
            )
            air_temp_c = bounded_gauss(
                rng, chamber_temp_c, FLUSH_TEMP_SD_C, TEMP_MIN_C, TEMP_MAX_C
            )

            rows.append(
                {
                    "chamber_id": chamber_id,
                    "substrate": substrate,
                    "flush_number": flush_number,
                    "flush_yield_g": "{:.1f}".format(yield_g),
                    "air_temp_c": "{:.1f}".format(air_temp_c),
                    "days_from_spawn": str(int(round(day))),
                }
            )

    rows.sort(key=lambda r: (r["chamber_id"], r["flush_number"]))

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
