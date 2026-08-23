"""Generate the simulated orchard fruit-firmness dataset.

Standard library only. Fixed seed, so re-running reproduces apple_firmness.csv
byte for byte.

Design encoded here:
  16 mature trees of one cultivar, 8 on the standard irrigation schedule and
  8 on the summer deficit schedule. 8 fruit picked from around the canopy of
  each tree, each fruit tested once with a penetrometer. 16 * 8 = 128 fruit.

Magnitudes:
  standard schedule group mean   63.0 N
  deficit schedule group mean    68.0 N
  tree-to-tree spread around the group mean   SD 3.0 N
  fruit-to-fruit spread within a tree         SD 4.0 N
  values rounded to 1 decimal, kept inside 50.0 - 82.0 N
"""

import csv
import random

SEED = 20260822
N_TREES = 16
N_FRUIT_PER_TREE = 8
GROUP_MEAN = {"standard": 63.0, "deficit": 68.0}
SD_TREE = 3.0
SD_FRUIT = 4.0
FIRMNESS_MIN = 50.0
FIRMNESS_MAX = 82.0
OUT_PATH = "apple_firmness.csv"


def draw_in_range(rng, mean, sd):
    """Normal draw, redrawn until it falls inside the plausible instrument range."""
    for _ in range(1000):
        value = rng.gauss(mean, sd)
        if FIRMNESS_MIN <= value <= FIRMNESS_MAX:
            return value
    raise RuntimeError("could not draw an in-range value")


def main():
    rng = random.Random(SEED)

    tree_codes = ["T-%02d" % i for i in range(1, N_TREES + 1)]
    schedules = ["standard"] * (N_TREES // 2) + ["deficit"] * (N_TREES // 2)
    rng.shuffle(schedules)
    assignment = dict(zip(tree_codes, schedules))

    rows = []
    for tree_code in tree_codes:
        schedule = assignment[tree_code]
        tree_mean = GROUP_MEAN[schedule] + rng.gauss(0.0, SD_TREE)
        for position in range(1, N_FRUIT_PER_TREE + 1):
            firmness = draw_in_range(rng, tree_mean, SD_FRUIT)
            rows.append(
                {
                    "tree_code": tree_code,
                    "irrigation": schedule,
                    "fruit_position": position,
                    "firmness_N": "%.1f" % firmness,
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["tree_code", "irrigation", "fruit_position", "firmness_N"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s with %d data rows" % (OUT_PATH, len(rows)))


if __name__ == "__main__":
    main()
