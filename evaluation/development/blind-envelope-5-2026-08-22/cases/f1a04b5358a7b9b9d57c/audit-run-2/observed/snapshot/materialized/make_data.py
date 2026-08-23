"""Generate the coffee agroforestry porometer data set.

Standard library only. Fixed seed so the file is reproducible byte-for-byte.

Design: 20 mature arabica shrubs on one estate, 10 under nitrogen-fixing shade
trees and 10 in full sun. Six fully expanded leaves per shrub were measured
individually with a porometer on a single clear morning -> 120 measured leaves.

Values are simulated with a shrub-level offset (rooting depth / crop load) plus
independent leaf-level variation on the same shrub.
"""

import csv
import os
import random

SEED = 20260822
random.seed(SEED)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "coffee_stomatal_conductance.csv")

N_PER_GROUP = 10
LEAVES_PER_SHRUB = 6

# Where on the canopy each of the six leaves sat.
LEAF_POSITIONS = [
    "upper_north",
    "upper_south",
    "mid_east",
    "mid_west",
    "lower_east",
    "lower_west",
]

# Group-level parameters for stomatal conductance (mmol H2O m-2 s-1).
#   mean      : group mean
#   shrub_sd  : between-shrub spread (rooting depth, crop load)
#   leaf_sd   : leaf-to-leaf spread within a shrub
#   lo / hi   : plausible field range, used to clip extremes
GROUPS = {
    "full_sun": dict(mean=158.0, shrub_sd=17.0, leaf_sd=14.0, lo=110, hi=210),
    "shade_trees": dict(mean=228.0, shrub_sd=24.0, leaf_sd=19.0, lo=160, hi=300),
}

# Leaf temperature (degrees C): shaded canopies run cooler on a clear morning.
TEMP = {
    "full_sun": dict(mean=29.6, shrub_sd=0.9, leaf_sd=1.0, lo=24.0, hi=33.0),
    "shade_trees": dict(mean=26.4, shrub_sd=0.8, leaf_sd=0.9, lo=24.0, hi=33.0),
}


def clip(value, lo, hi):
    return max(lo, min(hi, value))


def field_tags(n_total):
    """Field tags combining an estate row and a position within that row."""
    tags = []
    row = 2
    pos = 3
    for _ in range(n_total):
        tags.append("R{:02d}-P{:02d}".format(row, pos))
        pos += random.choice([2, 3, 4])
        if pos > 24:
            row += 1
            pos = random.choice([3, 4, 5])
    return tags


def main():
    tags = field_tags(N_PER_GROUP * 2)
    random.shuffle(tags)
    assignment = (
        [(tags[i], "shade_trees") for i in range(N_PER_GROUP)]
        + [(tags[i], "full_sun") for i in range(N_PER_GROUP, 2 * N_PER_GROUP)]
    )
    assignment.sort(key=lambda pair: pair[0])

    rows = []
    for shrub_label, treatment in assignment:
        gc = GROUPS[treatment]
        tc = TEMP[treatment]
        shrub_gc_offset = random.gauss(0.0, gc["shrub_sd"])
        shrub_tc_offset = random.gauss(0.0, tc["shrub_sd"])
        for position in LEAF_POSITIONS:
            conductance = gc["mean"] + shrub_gc_offset + random.gauss(0.0, gc["leaf_sd"])
            conductance = clip(conductance, gc["lo"], gc["hi"])

            temp = tc["mean"] + shrub_tc_offset + random.gauss(0.0, tc["leaf_sd"])
            # Leaves transpiring hardest cool themselves slightly.
            temp -= 0.010 * (conductance - gc["mean"])
            temp = clip(temp, tc["lo"], tc["hi"])

            rows.append(
                {
                    "shrub_label": shrub_label,
                    "canopy_treatment": treatment,
                    "leaf_position": position,
                    "leaf_temp_c": "{:.1f}".format(temp),
                    "stomatal_conductance_mmol_m2_s": str(int(round(conductance))),
                }
            )

    header = [
        "shrub_label",
        "canopy_treatment",
        "leaf_position",
        "leaf_temp_c",
        "stomatal_conductance_mmol_m2_s",
    ]
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} ({} data rows)".format(OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
