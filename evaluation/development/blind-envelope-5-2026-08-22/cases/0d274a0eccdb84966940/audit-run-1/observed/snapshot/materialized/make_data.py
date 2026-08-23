"""Generate the novel-object-recognition run-level dataset.

Study design: 18 adult male rats (9 enriched housing, 9 standard housing).
Each rat is run through 8 novel-object recognition tests on separate days,
giving 18 * 8 = 144 test runs (one row per run).

Values are simulated with a fixed seed so the file is reproducible.
Standard library only.
"""

import csv
import os
import random

SEED = 20260822
N_PER_GROUP = 9
RUNS_PER_RAT = 8

# Discrimination index model: a stable animal-level tendency plus run-to-run noise.
GROUP_PARAMS = {
    "standard": {"center": 0.570, "animal_sd": 0.026, "run_sd": 0.036},
    "enriched": {"center": 0.680, "animal_sd": 0.030, "run_sd": 0.040},
}
DI_FLOOR, DI_CEIL = 0.40, 0.90

# Total object exploration time per run, in seconds.
EXPL_MEAN, EXPL_SD, EXPL_MIN, EXPL_MAX = 29.0, 6.0, 15.0, 45.0

OUT_NAME = "data.csv"


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Realistic-looking animal codes: cohort letter + three digits.
    rat_ids = ["BN-%03d" % n for n in range(101, 101 + 2 * N_PER_GROUP)]
    housings = ["enriched"] * N_PER_GROUP + ["standard"] * N_PER_GROUP
    rng.shuffle(housings)
    assignment = list(zip(rat_ids, housings))

    rows = []
    for rat_id, housing in assignment:
        params = GROUP_PARAMS[housing]
        animal_offset = rng.gauss(0.0, params["animal_sd"])
        for run_number in range(1, RUNS_PER_RAT + 1):
            di = params["center"] + animal_offset + rng.gauss(0.0, params["run_sd"])
            di = clamp(di, DI_FLOOR, DI_CEIL)
            expl = clamp(rng.gauss(EXPL_MEAN, EXPL_SD), EXPL_MIN, EXPL_MAX)
            rows.append(
                {
                    "rat_id": rat_id,
                    "housing": housing,
                    "run_number": run_number,
                    "exploration_time_s": "%.1f" % expl,
                    "discrimination_index": "%.3f" % di,
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fields = [
        "rat_id",
        "housing",
        "run_number",
        "exploration_time_s",
        "discrimination_index",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
