"""Generate the simulated preclinical tumour-growth dataset.

Twenty-four tumour-bearing rats (12 vehicle, 12 treated) are each measured by
calliper once a week for five consecutive weeks, giving 120 rows and one CSV
file, tumour_volumes.csv.

All values are invented. Nothing here is measured data.

Generating model
----------------
    tumour_volume_mm3 = baseline
                        + group_slope * (week - 1)   fixed growth
                        + a_i                        animal intercept effect
                        + b_i * (week - 1)           animal slope effect
                        + e_it                       measurement noise

    baseline       = 180 mm3 in both groups
    group_slope    = 175 mm3/week (vehicle) -> about 880 mm3 at week 5
                   = 110 mm3/week (treated) -> about 620 mm3 at week 5
    a_i            Normal(0, 18 mm3)
    b_i            Normal(0, 29.5 mm3/week)
    e_it           Normal(0, 60 mm3)

The between-animal SD at week 5 is sqrt(18^2 + (4 * 29.5)^2) = 119 mm3, and the
measurement-to-measurement SD within an animal is 60 mm3, as the study design
calls for.

Because 12 animals per group is a small draw, the raw pseudo-random numbers
would leave the realised means and SDs several tens of mm3 away from those
targets. Each set of draws is therefore centred and rescaled to its intended
mean and SD before use: animal intercepts and slopes within each treatment
group, residuals across the whole file, and body-weight offsets across animals.
This is a deliberate choice so that the delivered file has the spread and the
group trajectories the design specifies. It makes the realised summary
statistics match the design values more tightly than a fresh sample of this size
usually would, and it means the residuals are not an independent random sample.

Body weight is about 280 g with a per-animal offset and a small weekly drift
(mildly upward on vehicle, mildly downward under treatment). Animals are housed
two per cage and cages never mix treatment groups, which is how such a study is
normally run; cage is therefore nested within treatment group and cannot be
separated from it.

Run with: /usr/local/bin/python3 make_data.py
Standard library only. No packages are installed.
"""

import csv
import os
import random

SEED = 20260822
N_PER_GROUP = 12
N_WEEKS = 5
GROUPS = ("vehicle", "treated")

BASELINE = 180.0
SLOPE = {"vehicle": 175.0, "treated": 110.0}

SD_ANIMAL_INTERCEPT = 18.0
SD_ANIMAL_SLOPE = 29.5
SD_RESIDUAL = 60.0

BODY_WEIGHT_MEAN = 280.0
SD_BODY_WEIGHT_ANIMAL = 12.0
SD_BODY_WEIGHT_NOISE = 3.5
WEEKLY_WEIGHT_DRIFT = {"vehicle": 1.6, "treated": -1.1}

OUT_NAME = "tumour_volumes.csv"
FIELDNAMES = [
    "animal_id",
    "treatment_group",
    "week",
    "tumour_volume_mm3",
    "body_weight_g",
    "cage",
]


def standardise(values, target_sd):
    """Centre a list of draws on zero and rescale it to exactly target_sd."""
    n = len(values)
    mean = sum(values) / n
    centred = [v - mean for v in values]
    var = sum(v * v for v in centred) / (n - 1)
    scale = target_sd / (var ** 0.5)
    return [v * scale for v in centred]


def build_rows(rng):
    # Animal-level effects, standardised within each treatment group.
    effects = {}
    for group in GROUPS:
        intercepts = standardise(
            [rng.gauss(0.0, 1.0) for _ in range(N_PER_GROUP)], SD_ANIMAL_INTERCEPT
        )
        slopes = standardise(
            [rng.gauss(0.0, 1.0) for _ in range(N_PER_GROUP)], SD_ANIMAL_SLOPE
        )
        weights = standardise(
            [rng.gauss(0.0, 1.0) for _ in range(N_PER_GROUP)], SD_BODY_WEIGHT_ANIMAL
        )
        effects[group] = list(zip(intercepts, slopes, weights))

    # Measurement noise, standardised across the whole file.
    n_rows = len(GROUPS) * N_PER_GROUP * N_WEEKS
    residuals = standardise([rng.gauss(0.0, 1.0) for _ in range(n_rows)], SD_RESIDUAL)
    weight_noise = standardise(
        [rng.gauss(0.0, 1.0) for _ in range(n_rows)], SD_BODY_WEIGHT_NOISE
    )

    rows = []
    animal_number = 0
    i = 0
    for group in GROUPS:
        prefix = "V" if group == "vehicle" else "T"
        for k, (a_i, b_i, w_i) in enumerate(effects[group]):
            animal_number += 1
            animal_id = "{}{:02d}".format(prefix, k + 1)
            # Two animals per cage; cages never mix treatment groups.
            cage = "cage_{:02d}".format((animal_number + 1) // 2)

            for week in range(1, N_WEEKS + 1):
                t = week - 1
                volume = (
                    BASELINE + SLOPE[group] * t + a_i + b_i * t + residuals[i]
                )
                weight = (
                    BODY_WEIGHT_MEAN
                    + w_i
                    + WEEKLY_WEIGHT_DRIFT[group] * t
                    + weight_noise[i]
                )
                i += 1

                if volume <= 0:
                    raise ValueError(
                        "generated a non-positive tumour volume for {} week {}".format(
                            animal_id, week
                        )
                    )

                rows.append(
                    {
                        "animal_id": animal_id,
                        "treatment_group": group,
                        "week": week,
                        "tumour_volume_mm3": round(volume, 1),
                        "body_weight_g": round(weight, 1),
                        "cage": cage,
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
