"""Generate the detector-night dataset for the river-valley lighting survey.

Twelve lesser horseshoe bat maternity roosts (six beside a newly lit footpath,
six in valleys that remain dark) each carried a static ultrasonic detector for
eight consecutive suitable nights. Every detector-night gives one activity
total (bat passes) and the nightly minimum temperature.

Standard library only. Fixed seed so the CSVs are reproducible.
"""

import csv
import math
import os
import random

SEED = 20260891
N_NIGHTS = 8
ROOSTS_PER_CONDITION = 6

# Nightly means we are aiming for, in bat passes per detector-night.
MEAN_DARK = 205.0
MEAN_LIT = 130.0

# Spread between roosts: big maternity roosts are busy every night, small ones
# are quiet every night. Log-scale SD of the roost multiplier.
ROOST_LOG_SD = 0.34

# Weather. Nightly minimum temperature runs roughly 4-15 C over the survey.
TEMP_CENTRE = 9.5
TEMP_BETA = 0.055        # proportional change in passes per degree C
NIGHT_LOG_SD = 0.10      # extra night-to-night weather wobble

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "bat_activity.csv")
SUMMARY_CSV = os.path.join(HERE, "roost_summary.csv")


def poisson_like(lam, rng):
    """Draw a whole count around lam with Poisson-scale sampling noise."""
    value = rng.normalvariate(lam, math.sqrt(lam))
    return max(0, int(round(value)))


def build_rows(rng):
    conditions = []
    for i in range(ROOSTS_PER_CONDITION):
        conditions.append("dark")
        conditions.append("lit")

    roosts = []
    for index, condition in enumerate(conditions, start=1):
        roosts.append(
            {
                "roost_code": "R%02d" % index,
                "lighting_condition": condition,
                # Roost size / quality multiplier, centred on 1.
                "roost_effect": math.exp(
                    rng.normalvariate(0.0, ROOST_LOG_SD) - 0.5 * ROOST_LOG_SD ** 2
                ),
            }
        )

    # Weather is shared across the valleys on a given night, so draw a nightly
    # baseline temperature and jitter it slightly per roost.
    night_temp = [rng.uniform(4.5, 14.5) for _ in range(N_NIGHTS)]

    rows = []
    for roost in roosts:
        base = MEAN_DARK if roost["lighting_condition"] == "dark" else MEAN_LIT
        for night in range(1, N_NIGHTS + 1):
            temp = night_temp[night - 1] + rng.normalvariate(0.0, 0.6)
            temp = min(15.0, max(4.0, temp))
            temp_effect = math.exp(TEMP_BETA * (temp - TEMP_CENTRE))
            wobble = math.exp(
                rng.normalvariate(0.0, NIGHT_LOG_SD) - 0.5 * NIGHT_LOG_SD ** 2
            )
            lam = base * roost["roost_effect"] * temp_effect * wobble
            rows.append(
                {
                    "roost_code": roost["roost_code"],
                    "lighting_condition": roost["lighting_condition"],
                    "night_index": night,
                    "min_temp_c": round(temp, 1),
                    "bat_passes": poisson_like(lam, rng),
                }
            )

    rows.sort(key=lambda r: (r["roost_code"], r["night_index"]))
    return rows


def write_detector_nights(rows):
    fields = [
        "roost_code",
        "lighting_condition",
        "night_index",
        "min_temp_c",
        "bat_passes",
    ]
    with open(DATA_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_roost_summary(rows):
    order = []
    grouped = {}
    for row in rows:
        code = row["roost_code"]
        if code not in grouped:
            grouped[code] = []
            order.append(code)
        grouped[code].append(row)

    fields = [
        "roost_code",
        "lighting_condition",
        "nights_surveyed",
        "total_passes",
        "mean_passes_per_night",
        "min_passes",
        "max_passes",
        "mean_min_temp_c",
    ]
    with open(SUMMARY_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for code in order:
            block = grouped[code]
            counts = [r["bat_passes"] for r in block]
            temps = [r["min_temp_c"] for r in block]
            writer.writerow(
                {
                    "roost_code": code,
                    "lighting_condition": block[0]["lighting_condition"],
                    "nights_surveyed": len(block),
                    "total_passes": sum(counts),
                    "mean_passes_per_night": round(sum(counts) / len(counts), 1),
                    "min_passes": min(counts),
                    "max_passes": max(counts),
                    "mean_min_temp_c": round(sum(temps) / len(temps), 1),
                }
            )


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)
    write_detector_nights(rows)
    write_roost_summary(rows)

    for condition in ("dark", "lit"):
        block = [r["bat_passes"] for r in rows if r["lighting_condition"] == condition]
        print(
            "%s: n=%d detector-nights, mean=%.1f, range %d-%d"
            % (condition, len(block), sum(block) / len(block), min(block), max(block))
        )


if __name__ == "__main__":
    main()
