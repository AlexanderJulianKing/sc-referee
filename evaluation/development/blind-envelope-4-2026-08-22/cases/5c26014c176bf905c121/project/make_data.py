"""
Generate the Pacific oyster stocking-density trial data.

Fourteen mesh grow-out baskets were hung along a single longline: seven at the
farm's standard stocking density and seven at a reduced stocking density. After
twenty weeks each basket was lifted and twelve oysters were removed from it and
measured, giving 14 x 12 = 168 measured oysters.

Shell height is built up from three pieces:
  1. a group mean (standard ~61.5 mm, reduced ~68.0 mm),
  2. a basket offset, because a basket's position along the longline shifts all
     of its oysters up or down by a few millimetres together (the seven offsets
     inside a group are re-centred on zero so the group means land on target),
  3. an oyster-level deviation with a standard deviation of about 6 mm.

Values are recorded to one decimal place and are resampled if they fall outside
the believable range of 45.0 to 85.0 mm.

Standard library only. The seed is fixed so the file is reproducible, and it was
chosen so that the realised group means land close to the intended 61.5 mm and
68.0 mm.
"""

import csv
import os
import random

SEED = 20260830
N_BASKETS_PER_GROUP = 7
N_OYSTERS_PER_BASKET = 12

GROUP_MEAN_MM = {"standard": 61.5, "reduced": 68.0}
BASKET_SD_MM = 2.8       # spread of basket offsets along the longline
MAX_BASKET_OFFSET_MM = 4.5  # no basket sits further than this from its group mean
OYSTER_SD_MM = 6.0       # oyster-to-oyster spread inside one basket
MIN_MM, MAX_MM = 45.0, 85.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oyster_shell_height.csv")


def main():
    rng = random.Random(SEED)

    # Baskets B01..B14. Alternate the two treatments along the line so that the
    # position effect is not confounded with the treatment.
    baskets = []
    for i in range(1, N_BASKETS_PER_GROUP * 2 + 1):
        group = "standard" if i % 2 == 1 else "reduced"
        baskets.append(("B%02d" % i, group))

    # Draw one offset per basket, then re-centre the seven offsets within each
    # group on zero so that the realised group means sit at the intended values
    # while the baskets still differ from one another.
    basket_offset = {}
    for group in GROUP_MEAN_MM:
        members = [bid for bid, g in baskets if g == group]
        while True:
            raw = [rng.gauss(0.0, BASKET_SD_MM) for _ in members]
            mean_raw = sum(raw) / len(raw)
            centred = [x - mean_raw for x in raw]
            # Keep the position effect to a few millimetres either way.
            if max(abs(x) for x in centred) <= MAX_BASKET_OFFSET_MM:
                break
        for bid, off in zip(members, centred):
            basket_offset[bid] = off

    rows = []
    for basket_id, group in baskets:
        basket_mean = GROUP_MEAN_MM[group] + basket_offset[basket_id]
        for oyster_number in range(1, N_OYSTERS_PER_BASKET + 1):
            while True:
                height = basket_mean + rng.gauss(0.0, OYSTER_SD_MM)
                height = round(height, 1)
                if MIN_MM <= height <= MAX_MM:
                    break
            rows.append([basket_id, group, oyster_number, "%.1f" % height])

    with open(OUT_PATH, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["basket_id", "density_group", "oyster_number", "shell_height_mm"])
        writer.writerows(rows)

    print("wrote %d data rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
