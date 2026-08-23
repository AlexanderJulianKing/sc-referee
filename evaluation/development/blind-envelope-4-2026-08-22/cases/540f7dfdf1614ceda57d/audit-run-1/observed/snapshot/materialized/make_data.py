"""Generate the raw core-sampling data for the composting bulking-agent trial.

Design: 16 full-scale windrows (8 woodchip, 8 straw), 5 spatial cores per
windrow, 80 core rows total. Each core value is built as

    c_to_n_ratio = group mean + windrow offset + core noise

with group means 18.5 (woodchip) and 15.2 (straw), a between-windrow SD of
1.2 and a within-windrow (core-to-core) SD of 1.6. Values are rounded to one
decimal place and held inside the believable range 11.0 to 24.0.

Standard library only. Fixed seed, so re-running reproduces the same file.
"""

import csv
import os
import random

SEED = 20260822

GROUP_MEANS = {"woodchip": 18.5, "straw": 15.2}
BETWEEN_WINDROW_SD = 1.2
WITHIN_WINDROW_SD = 1.6

N_WINDROWS_PER_GROUP = 8
N_CORES_PER_WINDROW = 5

MIN_RATIO = 11.0
MAX_RATIO = 24.0

COLUMNS = ["windrow_id", "bulking_agent", "core_number", "c_to_n_ratio"]
OUT_NAME = "compost_cores.csv"


def clamp(value, low=MIN_RATIO, high=MAX_RATIO):
    return max(low, min(high, value))


def build_rows(rng):
    rows = []
    # Windrows W01-W08 are woodchip, W09-W16 are straw.
    assignments = (
        ["woodchip"] * N_WINDROWS_PER_GROUP + ["straw"] * N_WINDROWS_PER_GROUP
    )
    for index, agent in enumerate(assignments, start=1):
        windrow_id = "W%02d" % index
        windrow_offset = rng.gauss(0.0, BETWEEN_WINDROW_SD)
        windrow_mean = GROUP_MEANS[agent] + windrow_offset
        for core_number in range(1, N_CORES_PER_WINDROW + 1):
            value = windrow_mean + rng.gauss(0.0, WITHIN_WINDROW_SD)
            rows.append(
                {
                    "windrow_id": windrow_id,
                    "bulking_agent": agent,
                    "core_number": core_number,
                    "c_to_n_ratio": round(clamp(value), 1),
                }
            )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %d data rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
