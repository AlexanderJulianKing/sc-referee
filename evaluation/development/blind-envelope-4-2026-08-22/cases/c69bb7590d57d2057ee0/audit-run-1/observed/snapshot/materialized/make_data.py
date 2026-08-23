"""Generate the simulated field data for the rice nitrogen top-dressing trial.

Creates two CSV files in the same directory as this script:

  hill_harvest_raw.csv     one row per harvested hill (108 rows)
  paddy_harvest_summary.csv  one row per paddy (18 rows)

Standard library only. Fixed seed so the files are reproducible.
"""

import csv
import os
import random

SEED = 20260841
N_PADDIES_PER_SCHEDULE = 9
HILLS_PER_PADDY = 6

SCHEDULE_MEAN_G = {"split": 42.0, "late": 47.0}
PADDY_SD_G = 3.0      # paddy-to-paddy variation (soil fertility, water depth)
HILL_SD_G = 5.0       # hill-to-hill variation within one paddy
YIELD_MIN_G = 26.0
YIELD_MAX_G = 64.0

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "hill_harvest_raw.csv")
SUMMARY_PATH = os.path.join(HERE, "paddy_harvest_summary.csv")


def main():
    rng = random.Random(SEED)

    # Paddies P-01..P-18. Schedules are interleaved across the paddy numbering
    # so that schedule is not confounded with the station's paddy ordering.
    schedules = ["split", "late"] * N_PADDIES_PER_SCHEDULE
    rng.shuffle(schedules)

    raw_rows = []
    summary_rows = []

    for index, schedule in enumerate(schedules, start=1):
        paddy_code = "P-%02d" % index
        paddy_effect = rng.gauss(0.0, PADDY_SD_G)
        paddy_mean = SCHEDULE_MEAN_G[schedule] + paddy_effect

        hill_yields = []
        for position in range(1, HILLS_PER_PADDY + 1):
            value = rng.gauss(paddy_mean, HILL_SD_G)
            value = min(max(value, YIELD_MIN_G), YIELD_MAX_G)
            value = round(value, 1)
            hill_yields.append(value)
            raw_rows.append(
                {
                    "paddy_code": paddy_code,
                    "nitrogen_schedule": schedule,
                    "hill_position": position,
                    "hill_grain_yield_g": "%.1f" % value,
                }
            )

        mean_hill_yield = round(sum(hill_yields) / len(hill_yields), 1)
        summary_rows.append(
            {
                "paddy_code": paddy_code,
                "nitrogen_schedule": schedule,
                "hills_sampled": HILLS_PER_PADDY,
                "mean_hill_yield_g": "%.1f" % mean_hill_yield,
            }
        )

    with open(RAW_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "paddy_code",
                "nitrogen_schedule",
                "hill_position",
                "hill_grain_yield_g",
            ],
        )
        writer.writeheader()
        writer.writerows(raw_rows)

    with open(SUMMARY_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "paddy_code",
                "nitrogen_schedule",
                "hills_sampled",
                "mean_hill_yield_g",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print("raw rows: %d" % len(raw_rows))
    print("summary rows: %d" % len(summary_rows))


if __name__ == "__main__":
    main()
