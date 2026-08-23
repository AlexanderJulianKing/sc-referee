"""Generate the interleukin-6 assay table for the RA vs. control serum study.

Thirty banked serum samples (fifteen control, fifteen RA), one sample per person.
Each sample is assayed three times on the same plate, giving ninety assay rows.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.
Run: /usr/local/bin/python3 make_data.py
"""

import csv
import math
import os
import random

SEED = 20260851
N_PER_GROUP = 15
N_REPLICATES = 3
FIRST_SAMPLE_NUMBER = 101

# Person-level (biological) distribution of IL-6 in each cohort, in pg/mL.
# Mean and standard deviation are given on the natural concentration scale and
# converted to lognormal parameters, which gives the right-skewed tail the
# assay actually shows.
GROUP_TARGETS = {
    "control": {"mean": 4.2, "sd": 2.4},
    "RA": {"mean": 7.8, "sd": 2.4},
}

# Technical replicate scatter: the three runs of one sample spread over a
# window drawn from 5-7 percent of that sample's own concentration.
SPREAD_MIN = 0.05
SPREAD_MAX = 0.07

# Plausible reporting ceilings for a person-level concentration, in pg/mL.
# Healthy volunteers stay in single figures; a few patients reach the low teens.
GROUP_CEILING = {"control": 9.0, "RA": 13.5}

MIN_REPORTABLE = 0.01  # pg/mL; concentrations never reach zero or below.


def lognormal_params(mean, sd):
    """Convert a natural-scale mean and sd to lognormal mu and sigma."""
    sigma = math.sqrt(math.log(1.0 + (sd * sd) / (mean * mean)))
    mu = math.log(mean) - 0.5 * sigma * sigma
    return mu, sigma


def build_rows(rng):
    rows = []
    sample_number = FIRST_SAMPLE_NUMBER

    for cohort in ("control", "RA"):
        mu, sigma = lognormal_params(
            GROUP_TARGETS[cohort]["mean"], GROUP_TARGETS[cohort]["sd"]
        )
        for _ in range(N_PER_GROUP):
            sample_ref = "S-%d" % sample_number
            sample_number += 1

            # True IL-6 concentration in this person's aliquot.
            while True:
                true_value = math.exp(rng.gauss(mu, sigma))
                if true_value <= GROUP_CEILING[cohort]:
                    break

            # Plate precision for this sample: draw three offsets, centre them,
            # then scale them so the highest and lowest run differ by the
            # target percentage of this sample's own concentration.
            offsets = [rng.gauss(0.0, 1.0) for _ in range(N_REPLICATES)]
            centre = sum(offsets) / N_REPLICATES
            offsets = [o - centre for o in offsets]
            span = max(offsets) - min(offsets)
            scale = rng.uniform(SPREAD_MIN, SPREAD_MAX) / span
            offsets = [o * scale for o in offsets]

            for replicate_run in range(1, N_REPLICATES + 1):
                measured = true_value * (1.0 + offsets[replicate_run - 1])
                measured = max(round(measured, 2), MIN_REPORTABLE)
                rows.append([sample_ref, cohort, replicate_run, "%.2f" % measured])

    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "il6_assay.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_ref", "cohort", "replicate_run", "il6_pg_ml"])
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
