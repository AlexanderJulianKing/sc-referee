"""Generate the synthetic farm-level maize trial dataset.

Standard library only. Fixed seed, so the CSV is reproducible byte-for-byte.

Design mirrored by the data:
  * 40 smallholder farms in one district, each farm an independent holding.
  * 20 farms allocated the improved drought-tolerant variety, 20 kept their
    own landrace seed.
  * Each farm's whole maize field was harvested and weighed once at the end of
    the season, so each farm contributes exactly one row and one yield value.

Yield is built as a group mean plus a season-rainfall effect plus independent
farm-to-farm noise (rainfall, soil, weeding effort), then clamped into the
plausible range for its group and rounded to two decimals.
"""

import csv
import os
import random

SEED = 20260822
N_PER_GROUP = 20

# Plausible yield windows, tonnes per hectare at 15% moisture.
YIELD_RANGE = {
    "landrace": (1.4, 3.0),
    "improved": (2.2, 4.1),
}
GROUP_MEAN = {
    "landrace": 2.15,
    "improved": 3.05,
}
GROUP_SD = {
    "landrace": 0.34,
    "improved": 0.40,
}

# Rainfall shifts yield a little: this is the slope in t/ha per mm, applied to
# the deviation of a farm's rainfall from the district mean rainfall.
RAIN_MEAN_MM = 600.0
RAIN_SLOPE = 0.0018

# Ward codes used by the district extension register.
WARDS = ["03", "05", "07", "11"]


def clamp(value, low, high):
    return max(low, min(high, value))


def main():
    rng = random.Random(SEED)

    # Build the 40 register codes first, then shuffle the allocation so that
    # seed type is not confounded with ward or with position in the register.
    codes = []
    for ward in WARDS:
        for n in range(1, 11):
            codes.append("MKN-%s-%03d" % (ward, n))
    rng.shuffle(codes)
    codes = sorted(codes[:40])

    assignment = ["improved"] * N_PER_GROUP + ["landrace"] * N_PER_GROUP
    rng.shuffle(assignment)

    rows = []
    for farm_id, seed_type in zip(codes, assignment):
        field_area_ha = round(rng.uniform(0.4, 2.5), 2)
        season_rainfall_mm = int(round(clamp(rng.gauss(600.0, 78.0), 420, 780)))

        rain_effect = RAIN_SLOPE * (season_rainfall_mm - RAIN_MEAN_MM)
        raw = rng.gauss(GROUP_MEAN[seed_type], GROUP_SD[seed_type]) + rain_effect
        low, high = YIELD_RANGE[seed_type]
        grain_yield_t_ha = round(clamp(raw, low, high), 2)

        rows.append(
            {
                "farm_id": farm_id,
                "seed_type": seed_type,
                "field_area_ha": "%.2f" % field_area_ha,
                "season_rainfall_mm": str(season_rainfall_mm),
                "grain_yield_t_ha": "%.2f" % grain_yield_t_ha,
            }
        )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maize_trial.csv")
    fields = [
        "farm_id",
        "seed_type",
        "field_area_ha",
        "season_rainfall_mm",
        "grain_yield_t_ha",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
