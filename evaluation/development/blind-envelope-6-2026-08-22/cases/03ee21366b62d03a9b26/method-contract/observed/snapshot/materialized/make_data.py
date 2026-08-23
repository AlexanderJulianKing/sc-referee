"""Generate the kit weaning-weight dataset for the doe-nutrition trial.

Standard library only. Fixed seed so the CSV is reproducible.

Design: 14 breeding does, 7 on the standard pelleted ration and 7 on the same
ration plus a linseed-oil supplement. Each doe raises one litter; every kit
that survives to weaning (day 35) is weighed individually. Litter sizes run
from 6 to 9 kits, so the group totals are unbalanced.

Weight model (grams):
    kit weight = group mean + doe (litter) offset + kit deviation
    group mean       610 standard, 675 supplemented
    doe offset       Normal(0, 45)   between-litter variation
    kit deviation    Normal(0, 65)   between-kit variation inside a litter
"""

import csv
import os
import random

SEED = 20260822

GROUP_MEAN_G = {"standard": 610.0, "supplemented": 675.0}
BETWEEN_LITTER_SD_G = 45.0
WITHIN_LITTER_SD_G = 65.0

MIN_LITTER_SIZE = 6
MAX_LITTER_SIZE = 9
DOES_PER_GROUP = 7

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "kit_weaning_weights.csv")


def build_rows(rng):
    rows = []
    doe_counter = 0
    for group in ("standard", "supplemented"):
        for _ in range(DOES_PER_GROUP):
            doe_counter += 1
            doe_id = "D%02d" % doe_counter
            litter_size = rng.randint(MIN_LITTER_SIZE, MAX_LITTER_SIZE)
            doe_offset = rng.gauss(0.0, BETWEEN_LITTER_SD_G)
            for kit_number in range(1, litter_size + 1):
                weight = (
                    GROUP_MEAN_G[group]
                    + doe_offset
                    + rng.gauss(0.0, WITHIN_LITTER_SD_G)
                )
                rows.append(
                    {
                        "doe_id": doe_id,
                        "diet_group": group,
                        "litter_size": litter_size,
                        "kit_number": kit_number,
                        "weaning_weight_g": round(weight, 1),
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    # Litter size must equal the number of kit rows recorded for that doe.
    counts = {}
    for row in rows:
        counts[row["doe_id"]] = counts.get(row["doe_id"], 0) + 1
    for row in rows:
        assert row["litter_size"] == counts[row["doe_id"]], row["doe_id"]

    fields = ["doe_id", "diet_group", "litter_size", "kit_number", "weaning_weight_g"]
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d kit rows, %d does)" % (OUT_CSV, len(rows), len(counts)))


if __name__ == "__main__":
    main()
