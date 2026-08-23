"""Generate the tagged-tree dataset for the commercial thinning study.

Design: 14 forest stands (7 thinned, 7 unthinned). The thinning prescription is
applied to the whole stand, so treatment is a stand-level attribute. Within each
stand 10 mature overstory trees are tagged and remeasured, giving 140 tagged
trees in total.

Generating model for the five-year DBH increment (cm):

    increment_ij = mu[treatment(i)] + stand_effect_i + tree_noise_ij

    mu[unthinned] = 3.2      mu[thinned] = 4.6
    stand_effect_i  ~ Normal(0, 0.6)   one draw per stand
    tree_noise_ij   ~ Normal(0, 0.9)   one draw per tagged tree

The 14 drawn stand effects are then centred and rescaled so that their realised
standard deviation is exactly 0.6 cm, which keeps the stated between-stand
spread from drifting on a single 14-draw sample. Trees are left as drawn.

Increments are rounded to two decimals and floored at 0.00 so no value is
negative. Stdlib only, fixed seed, so the CSV is reproducible byte-for-byte.
"""

import csv
import os
import random

SEED = 20260822
N_STANDS = 14
N_TREATED = 7
TREES_PER_STAND = 10

MEAN_BY_TREATMENT = {"unthinned": 3.2, "thinned": 4.6}
SD_BETWEEN_STANDS = 0.6
SD_WITHIN_STAND = 0.9

# Crown position of the tagged overstory trees, with the starting-diameter
# centre each class is drawn around (cm). Dominants are the largest crowns.
CROWN_CLASSES = [
    ("dominant", 0.30, 44.0),
    ("codominant", 0.50, 37.0),
    ("intermediate", 0.20, 30.0),
]
SD_START_DBH = 3.5

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tagged_tree_increment.csv")

FIELDNAMES = [
    "stand_code",
    "treatment",
    "tree_tag",
    "start_dbh_cm",
    "crown_class",
    "dbh_increment_cm",
]


def pick_crown_class(rng):
    draw = rng.random()
    cumulative = 0.0
    for name, weight, centre in CROWN_CLASSES:
        cumulative += weight
        if draw < cumulative:
            return name, centre
    name, _, centre = CROWN_CLASSES[-1]
    return name, centre


def main():
    rng = random.Random(SEED)

    # Treatment is assigned once per stand, alternating so that neither group
    # occupies a single contiguous block of stand codes.
    stand_codes = ["ST-%02d" % i for i in range(1, N_STANDS + 1)]
    assignments = ["thinned"] * N_TREATED + ["unthinned"] * (N_STANDS - N_TREATED)
    rng.shuffle(assignments)
    stand_treatment = dict(zip(stand_codes, assignments))

    # One stand-level effect per stand, then centred and rescaled to the stated
    # between-stand standard deviation.
    raw_effects = [rng.gauss(0.0, SD_BETWEEN_STANDS) for _ in stand_codes]
    mean_effect = sum(raw_effects) / len(raw_effects)
    centred = [e - mean_effect for e in raw_effects]
    realised_sd = (sum(e * e for e in centred) / (len(centred) - 1)) ** 0.5
    scale = SD_BETWEEN_STANDS / realised_sd
    stand_effects = dict(zip(stand_codes, [e * scale for e in centred]))

    rows = []
    for stand_code in stand_codes:
        treatment = stand_treatment[stand_code]
        stand_effect = stand_effects[stand_code]
        for tag_index in range(1, TREES_PER_STAND + 1):
            crown_class, dbh_centre = pick_crown_class(rng)
            start_dbh = rng.gauss(dbh_centre, SD_START_DBH)
            start_dbh = max(start_dbh, 20.0)
            increment = (
                MEAN_BY_TREATMENT[treatment]
                + stand_effect
                + rng.gauss(0.0, SD_WITHIN_STAND)
            )
            increment = max(increment, 0.0)
            rows.append(
                {
                    "stand_code": stand_code,
                    "treatment": treatment,
                    "tree_tag": "%s-T%02d" % (stand_code, tag_index),
                    "start_dbh_cm": round(start_dbh, 1),
                    "crown_class": crown_class,
                    "dbh_increment_cm": round(increment, 2),
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), OUT_PATH))
    for name in stand_codes:
        vals = [r["dbh_increment_cm"] for r in rows if r["stand_code"] == name]
        print("  %s %-9s n=%d mean=%.2f" % (name, stand_treatment[name], len(vals), sum(vals) / len(vals)))


if __name__ == "__main__":
    main()
