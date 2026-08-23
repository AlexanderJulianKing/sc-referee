"""Simulate the actigraphy sleep-efficiency data for the shift-rotation study.

Design
------
26 warehouse workers wear wrist actigraphy monitors for 7 consecutive nights.
13 workers are on a slowly rotating shift pattern, 13 on a rapidly rotating one.

Each worker has a personal usual sleep-efficiency level drawn around the mean of
that worker's rotation pattern (between-worker SD = 4.0 percentage points).
Each monitored night varies around that worker's own usual level
(within-worker SD = 5.0 percentage points).

Values are recorded to one decimal place and are held inside the plausible
actigraphy range of 55.0 to 99.0 percent.

Standard library only. Fixed seed, so the CSV is reproducible.

Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260881

N_PER_GROUP = 13
N_NIGHTS = 7

GROUP_MEANS = {"slow": 84.5, "rapid": 78.9}

SD_BETWEEN_WORKERS = 4.0
SD_WITHIN_WORKER = 5.0

FLOOR_PCT = 55.0
CEILING_PCT = 99.0

OUT_FILE = "sleep_efficiency.csv"
COLUMNS = ["worker_id", "rotation_pattern", "night_number", "sleep_efficiency_pct"]


def clamp(value, low, high):
    return max(low, min(high, value))


def build_rows(rng):
    """Return the night-level rows: one row per worker per monitored night."""
    rows = []

    # Workers WK-01..WK-13 are on the slow rotation, WK-14..WK-26 on the rapid one.
    assignments = ["slow"] * N_PER_GROUP + ["rapid"] * N_PER_GROUP

    for index, pattern in enumerate(assignments, start=1):
        worker_id = "WK-%02d" % index

        # This worker's own usual level.
        worker_level = rng.gauss(GROUP_MEANS[pattern], SD_BETWEEN_WORKERS)

        for night_number in range(1, N_NIGHTS + 1):
            night_value = rng.gauss(worker_level, SD_WITHIN_WORKER)
            night_value = clamp(round(night_value, 1), FLOOR_PCT, CEILING_PCT)
            rows.append(
                {
                    "worker_id": worker_id,
                    "rotation_pattern": pattern,
                    "night_number": night_number,
                    "sleep_efficiency_pct": "%.1f" % night_value,
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

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
