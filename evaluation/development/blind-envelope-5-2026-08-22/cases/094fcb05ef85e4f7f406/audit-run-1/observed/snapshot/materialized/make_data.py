"""Generate the herbage mass dataset for the upland sheep grazing rotation study.

Standard library only. Fixed seed so the file is reproducible.

Structure: 16 fenced paddocks, 8 assigned whole to the fast rotation and 8 to
continuous set-stocking. Ten fixed grid sampling points per paddock, so 160 rows.

Values are built in two layers so the file shows the nesting the study describes:
  1. a paddock-level offset standing in for aspect and drainage, which moves the
     whole paddock up or down together;
  2. a point-level offset standing in for within-paddock patchiness.
Sward height is generated from the same herbage draw plus measurement noise, so
the two measured columns move together the way they do in the field.
"""

import csv
import os
import random

SEED = 20260822
N_POINTS_PER_PADDOCK = 10

# Field names in the style of a hill farm's paddock register.
SET_STOCK_PADDOCKS = [
    "Whinny Knowe",
    "Lang Rigg",
    "Corrie Park",
    "Brackens Head",
    "Sheil Bank",
    "Muirside Fauld",
    "Peat Hags",
    "Rashy Haugh",
]

FAST_ROTATION_PADDOCKS = [
    "Stey Brae",
    "Cauldron Park",
    "Birken Shaw",
    "High Fell Intake",
    "Kirk Ley",
    "Slack Burn",
    "Windy Slap",
    "Nether Bught",
]

# Group-level generating parameters, in kg DM per hectare.
GROUP_PARAMS = {
    # group: (mean, paddock-to-paddock SD, within-paddock point SD, clip low, clip high)
    "set_stocking": (1545.0, 205.0, 205.0, 900.0, 2200.0),
    "fast_rotation": (2480.0, 265.0, 285.0, 1600.0, 3400.0),
}

# Sward height is tied to herbage mass by a simple linear relation plus noise.
HEIGHT_INTERCEPT = -2.35
HEIGHT_SLOPE = 0.00575
HEIGHT_NOISE_SD = 1.0
HEIGHT_MIN = 3.0
HEIGHT_MAX = 18.0


def draw_within(rng, mean, sd, low, high, max_tries=200):
    """Draw a normal value that falls inside [low, high].

    Values outside the plausible field range are redrawn rather than pushed onto
    the boundary, so no artificial stack of identical values builds up at a limit.
    """
    for _ in range(max_tries):
        value = rng.gauss(mean, sd)
        if low <= value <= high:
            return value
    return max(low, min(high, value))


def build_rows(rng):
    rows = []
    groups = [
        ("set_stocking", SET_STOCK_PADDOCKS),
        ("fast_rotation", FAST_ROTATION_PADDOCKS),
    ]
    for rotation, paddocks in groups:
        mean, paddock_sd, point_sd, lo, hi = GROUP_PARAMS[rotation]
        for paddock_name in paddocks:
            # One draw per paddock: aspect and drainage shift the whole paddock.
            paddock_mean = mean + rng.gauss(0.0, paddock_sd)
            for grid_point in range(1, N_POINTS_PER_PADDOCK + 1):
                herbage = draw_within(rng, paddock_mean, point_sd, lo, hi)
                expected_height = HEIGHT_INTERCEPT + HEIGHT_SLOPE * herbage
                height = draw_within(
                    rng, expected_height, HEIGHT_NOISE_SD, HEIGHT_MIN, HEIGHT_MAX
                )
                rows.append(
                    {
                        "paddock_name": paddock_name,
                        "rotation": rotation,
                        "grid_point": grid_point,
                        "sward_height_cm": round(height, 1),
                        "herbage_kg_dm_ha": int(round(herbage)),
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "herbage_mass.csv")
    fieldnames = [
        "paddock_name",
        "rotation",
        "grid_point",
        "sward_height_cm",
        "herbage_kg_dm_ha",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
