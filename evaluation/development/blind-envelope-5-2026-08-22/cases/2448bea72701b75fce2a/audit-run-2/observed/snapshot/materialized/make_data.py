"""Generate the classroom CO2 dataset for the schools ventilation-upgrade study.

Standard library only. Fixed seed, so re-running reproduces classroom_co2.csv byte for byte.

Structure of the simulated estate:
  16 primary school buildings, 8 with the ventilation upgrade and 8 without.
  Each building contributes 5 logged classrooms, giving 80 classroom records.

Each building gets its own baseline concentration (its "signature" from age,
airtightness and boiler schedule); rooms within a building vary around that
baseline, with a mild extra contribution from how many pupils are in the room.
"""

import csv
import os
import random

SEED = 20260822
N_BUILDINGS_PER_ARM = 8
ROOMS_PER_BUILDING = 5

# Plausible whole-file ranges for the mid-lesson mean concentration (ppm).
UNUPGRADED_RANGE = (1200, 2100)
UPGRADED_RANGE = (750, 1350)

# Building-level baseline distributions (ppm) at a reference occupancy of 25 pupils.
UNUPGRADED_BASELINE = (1640.0, 200.0)   # (mean, sd)
UPGRADED_BASELINE = (1040.0, 155.0)

ROOM_SD = 85.0          # room-to-room variation inside one building (ppm)
PUPIL_EFFECT = 7.0      # ppm added per pupil above a reference of 25
REFERENCE_PUPILS = 25

PUPILS_RANGE = (18, 32)

# Estate-management style building references: district letter block + asset number.
DISTRICTS = ["NW", "NE", "CE", "SW", "SE", "WE"]

# Classroom naming in the style used across the estate: year group plus house name,
# or a numbered teaching room on a given floor.
HOUSE_NAMES = [
    "Oak", "Willow", "Rowan", "Maple", "Hazel", "Birch", "Cedar", "Elm",
    "Alder", "Beech", "Holly", "Juniper", "Larch", "Poplar", "Sycamore", "Aspen",
]
YEAR_GROUPS = ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6"]


def make_building_refs(rng):
    """Unique estate references, e.g. 'EDU/NW/0417'."""
    refs = set()
    while len(refs) < 2 * N_BUILDINGS_PER_ARM:
        refs.add("EDU/%s/%04d" % (rng.choice(DISTRICTS), rng.randint(101, 9899)))
    return sorted(refs)


def make_room_labels(rng):
    """Five distinct classroom labels for one building."""
    houses = rng.sample(HOUSE_NAMES, ROOMS_PER_BUILDING)
    labels = []
    for house in houses:
        if rng.random() < 0.25:
            labels.append("Room %d%s" % (rng.randint(1, 3), rng.choice("ABC")))
        else:
            labels.append("%s %s" % (rng.choice(YEAR_GROUPS), house))
    # Guard against a duplicate produced by the numbered-room branch.
    seen, unique = set(), []
    for i, label in enumerate(labels):
        while label in seen:
            label = "%s %s" % (rng.choice(YEAR_GROUPS), houses[i])
        seen.add(label)
        unique.append(label)
    return unique


def make_building_rows(rng, ref, status, baseline_stats, valid_range):
    """Five classroom rows for one building, all inside the plausible range."""
    mean_baseline, sd_baseline = baseline_stats
    low, high = valid_range
    for _attempt in range(2000):
        baseline = rng.gauss(mean_baseline, sd_baseline)
        labels = make_room_labels(rng)
        rows = []
        for label in labels:
            pupils = rng.randint(*PUPILS_RANGE)
            co2 = baseline + rng.gauss(0.0, ROOM_SD) + PUPIL_EFFECT * (pupils - REFERENCE_PUPILS)
            rows.append([ref, status, label, pupils, int(round(co2))])
        if all(low <= row[4] <= high for row in rows):
            return rows
    raise RuntimeError("could not draw an in-range building for %s" % ref)


def main():
    rng = random.Random(SEED)
    refs = make_building_refs(rng)
    rng.shuffle(refs)
    upgraded_refs = refs[:N_BUILDINGS_PER_ARM]
    unupgraded_refs = refs[N_BUILDINGS_PER_ARM:]

    rows = []
    for ref in sorted(upgraded_refs):
        rows.extend(make_building_rows(rng, ref, "upgraded", UPGRADED_BASELINE, UPGRADED_RANGE))
    for ref in sorted(unupgraded_refs):
        rows.extend(make_building_rows(rng, ref, "unupgraded", UNUPGRADED_BASELINE, UNUPGRADED_RANGE))

    rows.sort(key=lambda r: (r[0], r[2]))

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classroom_co2.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["building_ref", "ventilation_status", "room_label", "pupils_present", "mean_co2_ppm"]
        )
        writer.writerows(rows)

    print("wrote %s with %d data rows" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
