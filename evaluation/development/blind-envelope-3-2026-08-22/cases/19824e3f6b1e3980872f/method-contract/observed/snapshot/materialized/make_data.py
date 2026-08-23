"""Generate the synthetic limnology survey data set for this project.

Design
------
16 lakes (8 with agricultural catchments, 8 with forested catchments), 6
open-water sampling stations per lake, 96 rows in total. Total phosphorus is
built as a lake-level mean plus station-level noise, so the six rows from one
lake are positively correlated and are not six independent observations.

Target moments for total phosphorus (micrograms per litre)
----------------------------------------------------------
    agricultural catchment mean         ~ 34
    forested catchment mean             ~ 12
    between-lake SD (within a group)    ~ 9
    within-lake, station-to-station SD  ~ 4

Constrained sampling
--------------------
Two quantities are drawn as blocks and redrawn until they satisfy explicit
acceptance rules, rather than taken from the first draw.

1. Lake means. Total phosphorus is a concentration: strictly positive, and an
   oligotrophic forested lake in this region does not sit below about 3 ug/L. A
   plain normal draw with mean 12 and SD 9 puts real probability mass below
   zero, so the eight means in a group are redrawn until every one clears the
   floor and the group's realised mean and between-lake SD are close to target.
   This truncation is why the realised forested between-lake SD is under the
   nominal 9 and the forested group is mildly right-skewed. DATA_DESCRIPTION.md
   reports the realised moments rather than assuming they equal the targets.

2. Lake areas. Basin size is a feature of the regional lake population, not a
   consequence of land use, so areas come from one common 5-300 ha range for
   both groups. An unconstrained draw of 16 areas can still separate the groups
   by chance, which would quietly make surface area a stand-in for catchment
   type and confound the comparison of interest. The block of 16 is therefore
   redrawn until the two groups overlap across the range and their mean areas
   are close. Station depth is derived from area, so this keeps depth
   unconfounded as well.

Run with:  /usr/local/bin/python3 make_data.py
Writes:    lake_phosphorus.csv
Standard library only. Fixed seed, so the file is reproducible.
"""

import csv
import math
import os
import random
import statistics

SEED = 20260822
N_LAKES_PER_GROUP = 8
N_STATIONS = 6
GROUPS = ("agricultural", "forested")

GROUP_MEAN = {"agricultural": 34.0, "forested": 12.0}
BETWEEN_LAKE_SD = 9.0
WITHIN_LAKE_SD = 4.0

# Acceptance rules for the block of 8 lake means in a group.
ACCEPT_MIN_LAKE_MEAN = 3.0      # ug/L, plausible floor for a clear forested lake
ACCEPT_MEAN_TOL = 0.8           # ug/L, realised group mean vs. target
ACCEPT_SD_RANGE = (7.0, 11.0)   # ug/L, realised between-lake SD per group
MIN_SAMPLE = 1.0                # ug/L, floor for an individual water sample

# Lake surface area, and the acceptance rules that keep it from tracking group.
AREA_MIN_HA = 5.0
AREA_MAX_HA = 300.0
ACCEPT_AREA_MEAN_GAP = 30.0     # ha, largest allowed gap between group mean areas
ACCEPT_AREA_LOW = 90.0          # ha, each group needs at least one lake below this
ACCEPT_AREA_HIGH = 210.0        # ha, and at least one above this

OUT_NAME = "lake_phosphorus.csv"

rng = random.Random(SEED)


def draw_group_lake_means(group):
    """Draw the 8 lake means for one group, as a block, until acceptable."""
    target = GROUP_MEAN[group]
    while True:
        means = [rng.gauss(target, BETWEEN_LAKE_SD) for _ in range(N_LAKES_PER_GROUP)]
        if min(means) < ACCEPT_MIN_LAKE_MEAN:
            continue
        if abs(statistics.mean(means) - target) > ACCEPT_MEAN_TOL:
            continue
        if not (ACCEPT_SD_RANGE[0] <= statistics.stdev(means) <= ACCEPT_SD_RANGE[1]):
            continue
        return means


def draw_areas():
    """Draw all 16 lake areas until the two groups overlap across the range.

    Returns {group: [8 areas]}.
    """
    while True:
        areas = {
            g: [rng.uniform(AREA_MIN_HA, AREA_MAX_HA) for _ in range(N_LAKES_PER_GROUP)]
            for g in GROUPS
        }
        gap = abs(statistics.mean(areas["agricultural"]) - statistics.mean(areas["forested"]))
        if gap > ACCEPT_AREA_MEAN_GAP:
            continue
        if any(min(v) > ACCEPT_AREA_LOW for v in areas.values()):
            continue
        if any(max(v) < ACCEPT_AREA_HIGH for v in areas.values()):
            continue
        return areas


def draw_sample(lake_mean):
    """Station-level total phosphorus, redrawn until positive."""
    while True:
        value = rng.gauss(lake_mean, WITHIN_LAKE_SD)
        if value >= MIN_SAMPLE:
            return value


lake_means = {g: draw_group_lake_means(g) for g in GROUPS}
lake_areas = draw_areas()

rows = []
lake_number = 0

for group in GROUPS:
    for lake_mean, area_ha in zip(lake_means[group], lake_areas[group]):
        lake_number += 1
        lake_id = "L{:02d}".format(lake_number)

        # Mean basin depth: larger basins are on average deeper, with scatter.
        lake_mean_depth = max(1.8, 2.0 + 0.8 * (area_ha ** 0.35) + rng.gauss(0.0, 1.1))

        for station in range(1, N_STATIONS + 1):
            tp = draw_sample(lake_mean)

            # Station depth scatters around the lake's mean depth. Open-water
            # stations are not placed shallower than 1.0 m.
            depth = max(1.0, rng.gauss(lake_mean_depth, 0.22 * lake_mean_depth))

            rows.append(
                {
                    "lake_id": lake_id,
                    "catchment_land_use": group,
                    "station_number": station,
                    "total_phosphorus_ug_l": round(tp, 1),
                    "water_depth_m": round(depth, 1),
                    "lake_area_ha": round(area_ha, 1),
                }
            )

fieldnames = [
    "lake_id",
    "catchment_land_use",
    "station_number",
    "total_phosphorus_ug_l",
    "water_depth_m",
    "lake_area_ha",
]

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
with open(out_path, "w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

print("wrote {} rows to {}".format(len(rows), out_path))
