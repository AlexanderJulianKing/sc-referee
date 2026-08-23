"""Generate the street-tree sap flow dataset.

Standard library only. Fixed random seed so the CSV is reproducible.

Design
------
20 street trees of the same species and nursery stock, planted along comparable
roads in one city: 10 in conventional compacted planting pits and 10 in
engineered structural-soil pits. Each tree carries a sap flow sensor. The mean
daily sap flow for a settled mid-month week is recorded once a month for six
months of the growing season (April-September).

20 trees x 6 months = 120 rows. One row is one tree in one month.

Structure of the simulated values
---------------------------------
    sap flow = pit design mean
             + tree offset        (trees differ from one another, SD ~4 L/day)
             + month effect       (shared weather swing across the city)
             + measurement noise  (per-reading sensor/estimation noise)

The month effects and the tree offsets are drawn at random and then centred and
rescaled to their target spread, so the group means land on the intended
14 and 19 L/day and the weather pattern has no net level shift. The month
effect and the noise together move one tree by about 3 L/day month to month.
Values are clipped to the plausible sensor range 4-33 L/day and rounded to
0.1 L/day, the resolution the loggers report.
"""

import csv
import os
import random
import statistics

SEED = 20260823
N_PER_ARM = 10
MONTHS = ["April", "May", "June", "July", "August", "September"]

PIT_MEANS = {
    "conventional": 14.0,      # L/day
    "structural_soil": 19.0,   # L/day
}

BETWEEN_TREE_SD = 4.0   # trees differ from each other
MONTH_WEATHER_SD = 1.8  # shared month-to-month weather swing
RESIDUAL_SD = 2.4       # per-reading measurement noise
# month effect + noise => one tree moves ~sqrt(1.8^2 + 2.4^2) = 3.0 L/day

FLOOR = 4.0
CEILING = 33.0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "sap_flow.csv")


def centre_and_scale(values, target_sd):
    """Centre a list of draws on zero and rescale it to the target SD."""
    mean = statistics.fmean(values)
    centred = [v - mean for v in values]
    sd = statistics.pstdev(centred)
    if sd == 0:
        return centred
    return [v * target_sd / sd for v in centred]


def main():
    rng = random.Random(SEED)

    # One shared weather deviation per month, common to every tree in the city.
    month_effect = dict(
        zip(
            MONTHS,
            centre_and_scale(
                [rng.gauss(0.0, MONTH_WEATHER_SD) for _ in MONTHS],
                MONTH_WEATHER_SD,
            ),
        )
    )

    trees = []
    for i in range(N_PER_ARM):
        trees.append(("T%02d" % (i + 1), "conventional"))
    for i in range(N_PER_ARM):
        trees.append(("T%02d" % (N_PER_ARM + i + 1), "structural_soil"))

    # Tree-level offsets, centred within each planting arm.
    tree_offset = {}
    for arm in ("conventional", "structural_soil"):
        ids = [t for t, a in trees if a == arm]
        offsets = centre_and_scale(
            [rng.gauss(0.0, BETWEEN_TREE_SD) for _ in ids], BETWEEN_TREE_SD
        )
        tree_offset.update(dict(zip(ids, offsets)))

    rows = []
    for tree_id, pit_design in trees:
        for month in MONTHS:
            value = (
                PIT_MEANS[pit_design]
                + tree_offset[tree_id]
                + month_effect[month]
                + rng.gauss(0.0, RESIDUAL_SD)
            )
            value = min(CEILING, max(FLOOR, value))
            rows.append(
                {
                    "tree_id": tree_id,
                    "pit_design": pit_design,
                    "measurement_month": month,
                    "mean_daily_sap_flow_l_per_day": "%.1f" % value,
                }
            )

    fieldnames = [
        "tree_id",
        "pit_design",
        "measurement_month",
        "mean_daily_sap_flow_l_per_day",
    ]
    with open(OUT_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
