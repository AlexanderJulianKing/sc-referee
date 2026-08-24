"""Generate the hepatic lead dataset for the grey squirrel trace-metal study.

Standard library only. Fixed seed for reproducibility.

Design
------
26 squirrels (13 inner-city park, 13 rural woodland). Each animal's liver was
freeze-dried and homogenised once; that single homogenate was digested and read
three times on the same instrument. So each animal has one true homogenate
concentration, and the three readings are that value plus small instrument
error.

Between-animal spread is large (lognormal around the group centre); within-animal
analytical error is a few percent (multiplicative, CV ~3%).
"""

import csv
import hashlib
import math
import os
import random

SEED = 20260824

# Group centres on the mg/kg dry-weight scale.
GROUP_MEDIAN = {"urban_park": 0.365, "rural_woodland": 0.118}
# Between-animal spread on the log scale.
GROUP_LOG_SD = {"urban_park": 0.44, "rural_woodland": 0.46}

N_PER_GROUP = 13
N_RUNS = 3
ANALYTICAL_CV = 0.030          # ~3% relative repeatability of the instrument
PLAUSIBLE_RANGE = (0.040, 0.700)

OUT_NAME = "squirrel_liver_lead.csv"
FIELDS = ["squirrel_tag", "collection_setting", "analytical_run", "lead_mg_per_kg_dw"]


def draw_animal_means(rng):
    """One true homogenate concentration per animal, kept inside the plausible range."""
    animals = []
    tag_number = 101
    for setting in ("urban_park", "rural_woodland"):
        median = GROUP_MEDIAN[setting]
        log_sd = GROUP_LOG_SD[setting]
        for _ in range(N_PER_GROUP):
            while True:
                value = median * math.exp(rng.gauss(0.0, log_sd))
                if PLAUSIBLE_RANGE[0] <= value <= PLAUSIBLE_RANGE[1]:
                    break
            animals.append(("SQ-%d" % tag_number, setting, value))
            tag_number += 1
    return animals


def main():
    rng = random.Random(SEED)
    animals = draw_animal_means(rng)

    rows = []
    for tag, setting, true_value in animals:
        for run in range(1, N_RUNS + 1):
            reading = true_value * math.exp(rng.gauss(0.0, ANALYTICAL_CV))
            rows.append(
                {
                    "squirrel_tag": tag,
                    "collection_setting": setting,
                    "analytical_run": run,
                    "lead_mg_per_kg_dw": "%.4f" % reading,
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    with open(out_path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    print("wrote %s: %d data rows" % (OUT_NAME, len(rows)))
    print("sha256 %s" % digest)


if __name__ == "__main__":
    main()
