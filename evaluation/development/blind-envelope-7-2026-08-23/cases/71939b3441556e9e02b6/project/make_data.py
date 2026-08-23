"""Generate the olive grove irrigation trial data set.

Sixteen mature olive trees, eight under full-season irrigation and eight under
regulated deficit irrigation during pit hardening. At harvest, fruit was picked
from the four cardinal quadrants of each tree's canopy and each quadrant sample
was pressed and assayed for oil content, giving 16 x 4 = 64 rows.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260823

N_TREES = 16
POSITIONS = ["north", "east", "south", "west"]

REGIME_MEAN = {
    "full": 18.5,      # full-season irrigation
    "deficit": 21.3,   # regulated deficit irrigation at pit hardening
}

SD_BETWEEN_TREES = 1.1   # tree-to-tree spread on top of the regime mean
SD_WITHIN_TREE = 1.4     # canopy-position scatter about a tree's own mean
MAX_TREE_EFFECT = 2.5 * SD_BETWEEN_TREES  # keep any one tree from running away

OIL_MIN = 14.0
OIL_MAX = 26.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "olive_oil_content.csv")


def main():
    rng = random.Random(SEED)

    # Eight trees per regime, assignment scattered across the grove's tree numbers.
    tree_numbers = list(range(1, N_TREES + 1))
    regimes = ["full"] * 8 + ["deficit"] * 8
    rng.shuffle(regimes)
    assignment = dict(zip(tree_numbers, regimes))

    rows = []
    for number in tree_numbers:
        regime = assignment[number]
        tree_id = "T{:02d}".format(number)
        tree_effect = rng.gauss(0.0, SD_BETWEEN_TREES)
        while abs(tree_effect) > MAX_TREE_EFFECT:
            tree_effect = rng.gauss(0.0, SD_BETWEEN_TREES)
        tree_mean = REGIME_MEAN[regime] + tree_effect
        for position in POSITIONS:
            # Redraw rather than clip, so no assay lands exactly on a bound.
            value = tree_mean + rng.gauss(0.0, SD_WITHIN_TREE)
            while not (OIL_MIN <= value <= OIL_MAX):
                value = tree_mean + rng.gauss(0.0, SD_WITHIN_TREE)
            rows.append(
                {
                    "tree_id": tree_id,
                    "irrigation_regime": regime,
                    "canopy_position": position,
                    "oil_content_pct": "{:.2f}".format(value),
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["tree_id", "irrigation_regime", "canopy_position", "oil_content_pct"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
