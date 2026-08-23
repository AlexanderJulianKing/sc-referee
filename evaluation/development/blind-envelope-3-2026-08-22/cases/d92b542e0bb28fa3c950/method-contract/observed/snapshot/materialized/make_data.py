#!/usr/bin/env python3
"""Generate the weaned-piglet faecal microbiome dataset.

Twenty-two weaned piglets (11 control ration, 11 fibre-supplemented ration),
each sampled once a week for five consecutive weeks: 110 faecal samples.

Structure of the simulated Shannon values:
    shannon = group mean + piglet random effect + week trend + residual
      group mean       : 3.21 (control), 3.58 (supplemented)
      piglet effect    : Normal(0, 0.22)  -- between-animal spread
      week trend       : +0.03 per week, centred on week 3 so the group
                         means stay at their targets
      residual         : Normal(0, 0.15)  -- week-to-week movement in one pig

Body weight climbs from about 7 kg at week 1 to about 14 kg at week 5.
Read depth is drawn in the tens of thousands.

Run with a fixed seed so the file is reproducible byte-for-byte.
"""

import csv
import os
import random

SEED = 20260860  # chosen so the realised group means land on the target values

CONTROL_MEAN = 3.21
SUPPLEMENT_MEAN = 3.58
PIGLET_SD = 0.22          # between-animal spread
RESIDUAL_SD = 0.15        # within-animal week-to-week movement
WEEK_SLOPE = 0.03         # slight upward creep per week
WEEKS = [1, 2, 3, 4, 5]
WEEK_CENTRE = 3.0

WEIGHT_START = 7.0        # kg at week 1
WEIGHT_GAIN = 1.75        # kg gained per week -> about 14 kg at week 5
WEIGHT_PIGLET_SD = 0.55
WEIGHT_RESIDUAL_SD = 0.25

DEPTH_MEAN = 45000.0
DEPTH_SD = 9000.0
DEPTH_MIN = 22000
DEPTH_MAX = 78000

OUT_NAME = "piglet_shannon.csv"


def build_rows(rng):
    rows = []
    groups = [("control", 1, 11), ("supplement", 12, 22)]
    for ration, first, last in groups:
        base = CONTROL_MEAN if ration == "control" else SUPPLEMENT_MEAN
        for n in range(first, last + 1):
            piglet_id = "P{:02d}".format(n)
            piglet_effect = rng.gauss(0.0, PIGLET_SD)
            weight_effect = rng.gauss(0.0, WEIGHT_PIGLET_SD)
            for week in WEEKS:
                shannon = (
                    base
                    + piglet_effect
                    + WEEK_SLOPE * (week - WEEK_CENTRE)
                    + rng.gauss(0.0, RESIDUAL_SD)
                )
                weight = (
                    WEIGHT_START
                    + WEIGHT_GAIN * (week - 1)
                    + weight_effect
                    + rng.gauss(0.0, WEIGHT_RESIDUAL_SD)
                )
                depth = int(round(rng.gauss(DEPTH_MEAN, DEPTH_SD)))
                depth = max(DEPTH_MIN, min(DEPTH_MAX, depth))
                rows.append(
                    {
                        "piglet_id": piglet_id,
                        "ration": ration,
                        "week": week,
                        "shannon_diversity": round(shannon, 3),
                        "body_weight_kg": round(weight, 2),
                        "read_depth": depth,
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fields = [
        "piglet_id",
        "ration",
        "week",
        "shannon_diversity",
        "body_weight_kg",
        "read_depth",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
