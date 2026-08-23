"""Generate the rock-pool shading field data set.

Twelve intertidal rock pools (6 shaded with a mesh canopy, 6 uncovered).
Each pool sampled at 5 fixed points on its inner wall after 8 weeks.

Target structure:
  shaded pools    mean chlorophyll-a ~ 4.1 ug/cm2
  uncovered pools mean chlorophyll-a ~ 6.8 ug/cm2
  between-pool SD ~ 1.3 ug/cm2
  within-pool (point-to-point) SD ~ 0.7 ug/cm2

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20261612
N_POOLS_PER_GROUP = 6
N_POINTS = 5

GROUP_MEAN = {"shaded": 4.1, "uncovered": 6.8}
SD_BETWEEN_POOLS = 1.3
SD_WITHIN_POOL = 0.7

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "rockpool_chlorophyll.csv")


def main():
    rng = random.Random(SEED)

    # Pools alternate along the shore stretch; treatment assigned at the pool level.
    pools = []
    for i in range(N_POOLS_PER_GROUP):
        pools.append(("shaded", i))
        pools.append(("uncovered", i))
    pools.sort(key=lambda p: (p[1], p[0]))

    rows = []
    pool_number = 0
    for treatment, _ in pools:
        pool_number += 1
        pool_id = "P%02d" % pool_number

        # Pool-level random effect.
        pool_offset = rng.gauss(0.0, SD_BETWEEN_POOLS)
        pool_true = GROUP_MEAN[treatment] + pool_offset

        # Physical descriptor of the pool, constant within a pool.
        surface_area_m2 = round(max(0.15, rng.gauss(0.85, 0.30)), 2)

        for point in range(1, N_POINTS + 1):
            value = pool_true + rng.gauss(0.0, SD_WITHIN_POOL)
            value = max(0.2, value)
            rows.append(
                {
                    "pool_id": pool_id,
                    "treatment": treatment,
                    "point_id": "S%d" % point,
                    "chlorophyll_ug_cm2": round(value, 2),
                    "surface_area_m2": surface_area_m2,
                }
            )

    fields = [
        "pool_id",
        "treatment",
        "point_id",
        "chlorophyll_ug_cm2",
        "surface_area_m2",
    ]
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), OUT_CSV))


if __name__ == "__main__":
    main()
