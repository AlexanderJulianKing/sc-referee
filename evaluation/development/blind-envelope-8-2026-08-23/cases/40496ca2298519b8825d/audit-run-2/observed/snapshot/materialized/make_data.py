"""Generate the synthetic well-nitrate monitoring data for the catchment study.

Creates two CSV files in the same directory as this script:

  nitrate_monitoring_log.csv  raw log, one row per well-month (132 rows)
  well_nitrate_summary.csv    analysis-ready summary, one row per well (22 rows)

Standard library only. Fixed random seed, so re-running reproduces the files
byte for byte.

Generating model
----------------
Nitrate concentration for well i in month t:

    nitrate[i, t] = well_level[i] + noise[i, t]

well_level[i] is a persistent per-well level drawn around its catchment mean
(2.0 mg/L forested, 7.5 mg/L agricultural) with a large between-well spread.
noise[i, t] is independent month-to-month variation with SD 1.0 mg/L. Every
draw is bounded by rejection sampling rather than by clipping, so no value
piles up on a limit.

Water temperature carries a seasonal swing plus a per-well offset. Well depth
is a fixed property of the well, so it repeats unchanged across that well's
six rows.
"""

import csv
import os
import random

SEED = 20260823

N_WELLS_PER_GROUP = 11
N_WELLS = 2 * N_WELLS_PER_GROUP
MONTHS = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
N_MONTHS = len(MONTHS)

# Nitrate model, mg/L.
GROUP_MEAN = {"forested": 2.0, "agricultural": 7.5}
GROUP_BETWEEN_WELL_SD = {"forested": 0.8, "agricultural": 2.3}
# Plausible band for a well's persistent level, kept clear of the reporting
# limits so month-to-month noise rarely has to be rejected.
GROUP_LEVEL_RANGE = {"forested": (1.2, 4.5), "agricultural": (4.0, 12.0)}
WITHIN_WELL_SD = 1.0
NITRATE_MIN = 0.4
NITRATE_MAX = 14.0

# Water temperature model, degrees C. Seasonal offsets run Jan-Jun.
TEMP_BASE = 11.5
TEMP_SEASONAL = [-1.9, -1.6, -0.8, 0.4, 1.4, 2.1]
TEMP_WELL_SD = 0.8
TEMP_NOISE_SD = 0.35
TEMP_MIN = 8.0
TEMP_MAX = 15.0

# Well depth, metres. Fixed per well.
DEPTH_SD = 20.0
DEPTH_CENTRE = {"agricultural": 45.0, "forested": 70.0}
DEPTH_MIN = 15.0
DEPTH_MAX = 120.0


def truncated_gauss(rng, mu, sigma, low, high):
    """Normal draw restricted to [low, high] by rejection sampling.

    Rejection keeps the shape of the distribution inside the bounds. Clipping
    would instead stack every out-of-range draw onto the boundary value, which
    would show up in the data as an implausible spike at exactly 0.4 mg/L.
    """
    for _ in range(1000):
        value = rng.gauss(mu, sigma)
        if low <= value <= high:
            return value
    raise RuntimeError("truncated_gauss failed to draw inside [%r, %r]" % (low, high))


RAW_FIELDS = [
    "well_id",
    "catchment_type",
    "sample_month",
    "nitrate_mg_per_l",
    "water_temp_c",
    "well_depth_m",
]
SUMMARY_FIELDS = [
    "well_id",
    "catchment_type",
    "mean_nitrate_mg_per_l",
    "n_samples",
]


def build_wells(rng):
    """Assign catchment type and fixed per-well properties to WEL01..WEL22."""
    labels = ["agricultural"] * N_WELLS_PER_GROUP + ["forested"] * N_WELLS_PER_GROUP
    rng.shuffle(labels)

    wells = []
    for index, catchment_type in enumerate(labels, start=1):
        low, high = GROUP_LEVEL_RANGE[catchment_type]
        well_level = truncated_gauss(
            rng,
            GROUP_MEAN[catchment_type],
            GROUP_BETWEEN_WELL_SD[catchment_type],
            low,
            high,
        )
        # Agricultural wells tend to be shallower; forested wells sit deeper.
        depth = truncated_gauss(
            rng, DEPTH_CENTRE[catchment_type], DEPTH_SD, DEPTH_MIN, DEPTH_MAX
        )
        wells.append(
            {
                "well_id": "WEL%02d" % index,
                "catchment_type": catchment_type,
                "well_level": well_level,
                "temp_offset": rng.gauss(0.0, TEMP_WELL_SD),
                "well_depth_m": round(depth, 1),
            }
        )
    return wells


def build_rows(wells, rng):
    """One row per well per month, in well then month order."""
    rows = []
    for well in wells:
        for month_index, month in enumerate(MONTHS):
            nitrate = truncated_gauss(
                rng, well["well_level"], WITHIN_WELL_SD, NITRATE_MIN, NITRATE_MAX
            )
            temp_mu = TEMP_BASE + TEMP_SEASONAL[month_index] + well["temp_offset"]
            temp = truncated_gauss(rng, temp_mu, TEMP_NOISE_SD, TEMP_MIN, TEMP_MAX)

            rows.append(
                {
                    "well_id": well["well_id"],
                    "catchment_type": well["catchment_type"],
                    "sample_month": month,
                    "nitrate_mg_per_l": round(nitrate, 2),
                    "water_temp_c": round(temp, 1),
                    "well_depth_m": well["well_depth_m"],
                }
            )
    return rows


def build_summary(rows):
    """Collapse the raw rows to one row per well.

    The mean is taken over the rounded values written to the raw file, so the
    two files agree exactly when a reader recomputes the mean from the log.
    """
    order = []
    values = {}
    catchment = {}
    for row in rows:
        well_id = row["well_id"]
        if well_id not in values:
            order.append(well_id)
            values[well_id] = []
            catchment[well_id] = row["catchment_type"]
        values[well_id].append(row["nitrate_mg_per_l"])

    summary = []
    for well_id in order:
        well_values = values[well_id]
        mean_value = sum(well_values) / len(well_values)
        summary.append(
            {
                "well_id": well_id,
                "catchment_type": catchment[well_id],
                "mean_nitrate_mg_per_l": round(mean_value, 3),
                "n_samples": len(well_values),
            }
        )
    return summary


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rng = random.Random(SEED)
    wells = build_wells(rng)
    rows = build_rows(wells, rng)
    summary = build_summary(rows)

    here = os.path.dirname(os.path.abspath(__file__))
    write_csv(os.path.join(here, "nitrate_monitoring_log.csv"), RAW_FIELDS, rows)
    write_csv(os.path.join(here, "well_nitrate_summary.csv"), SUMMARY_FIELDS, summary)

    print("wells: %d" % len(wells))
    print("raw rows: %d" % len(rows))
    print("summary rows: %d" % len(summary))


if __name__ == "__main__":
    main()
