"""Generate the raw sprint-power dataset for the dietary nitrate study.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design simulated here:
  * 18 trained cyclists (RDR01 .. RDR18), 9 randomised to supplement, 9 to placebo.
  * Each rider performs 5 maximal seated sprints in one session.
  * One row per rider per sprint -> 18 * 5 = 90 rows.

Value model (all quantities in the units carried by the column names):
  * Between-rider differences are large and persistent: each rider gets a
    personal intercept built from body mass plus an independent rider effect.
  * Within-rider sprint-to-sprint noise is about 35 W.
  * Peak power drifts down across the five sprints as fatigue accumulates.
"""

import csv
import os
import random

# Seed choice: seeds were scanned only so that the realised group means land on
# the means the study description specifies (placebo ~880 W, supplement ~935 W)
# and the realised power range covers the stated ~680-1180 W envelope. No test
# statistic or p-value was computed during that scan; no analysis existed yet.
SEED = 2899
N_RIDERS = 18
N_PER_GROUP = 9
N_SPRINTS = 5

# Group targets for mean peak power, averaged over the five sprints.
GROUP_TARGET_W = {"placebo": 880.0, "supplement": 935.0}

FATIGUE_W_PER_SPRINT = -7.5      # slope on sprint_number (1..5)
WITHIN_RIDER_SD_W = 35.0         # sprint-to-sprint variation inside one rider
RIDER_EFFECT_SD_W = 55.0         # persistent rider-to-rider variation
MASS_SLOPE_W_PER_KG = 6.0        # heavier riders make more absolute power
MASS_MEAN_KG = 75.0
MASS_SD_KG = 6.0
MASS_MIN_KG, MASS_MAX_KG = 62.0, 88.0
POWER_MIN_W, POWER_MAX_W = 680.0, 1180.0

CADENCE_MEAN_RPM = 121.0
CADENCE_RIDER_SD_RPM = 4.5
CADENCE_WITHIN_SD_RPM = 2.5
CADENCE_DRIFT_RPM_PER_SPRINT = -1.1

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "sprint_power.csv")

MEAN_SPRINT_NUMBER = (N_SPRINTS + 1) / 2.0  # 3.0


def clamp(value, low, high):
    return max(low, min(high, value))


def build_rows(seed):
    """Return the full list of row dicts for a given random seed."""
    rng = random.Random(seed)

    rider_ids = ["RDR%02d" % i for i in range(1, N_RIDERS + 1)]

    # Randomised allocation: 9 supplement, 9 placebo.
    allocation = ["supplement"] * N_PER_GROUP + ["placebo"] * N_PER_GROUP
    rng.shuffle(allocation)
    group_of = dict(zip(rider_ids, allocation))

    rows = []
    for rider_id in rider_ids:
        group = group_of[rider_id]

        body_mass_kg = clamp(
            rng.gauss(MASS_MEAN_KG, MASS_SD_KG), MASS_MIN_KG, MASS_MAX_KG
        )

        # Rider intercept, expressed so the group's across-sprint mean lands on
        # the group target once the fatigue drift is added back in.
        rider_intercept_w = (
            GROUP_TARGET_W[group]
            - FATIGUE_W_PER_SPRINT * MEAN_SPRINT_NUMBER
            + MASS_SLOPE_W_PER_KG * (body_mass_kg - MASS_MEAN_KG)
            + rng.gauss(0.0, RIDER_EFFECT_SD_W)
        )

        rider_cadence_rpm = rng.gauss(CADENCE_MEAN_RPM, CADENCE_RIDER_SD_RPM)

        for sprint_number in range(1, N_SPRINTS + 1):
            peak_power_w = (
                rider_intercept_w
                + FATIGUE_W_PER_SPRINT * sprint_number
                + rng.gauss(0.0, WITHIN_RIDER_SD_W)
            )
            peak_power_w = clamp(peak_power_w, POWER_MIN_W, POWER_MAX_W)

            cadence_rpm = (
                rider_cadence_rpm
                + CADENCE_DRIFT_RPM_PER_SPRINT * (sprint_number - 1)
                + rng.gauss(0.0, CADENCE_WITHIN_SD_RPM)
            )

            rows.append(
                {
                    "rider_id": rider_id,
                    "supplement_group": group,
                    "sprint_number": sprint_number,
                    "peak_power_w": int(round(peak_power_w)),
                    "body_mass_kg": round(body_mass_kg, 1),
                    "cadence_rpm": round(cadence_rpm, 1),
                }
            )

    return rows


FIELDNAMES = [
    "rider_id",
    "supplement_group",
    "sprint_number",
    "peak_power_w",
    "body_mass_kg",
    "cadence_rpm",
]


def main():
    rows = build_rows(SEED)
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
