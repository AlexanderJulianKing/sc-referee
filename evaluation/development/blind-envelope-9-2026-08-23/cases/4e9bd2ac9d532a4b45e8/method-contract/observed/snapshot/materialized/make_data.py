"""Generate the simulated data for the bone-density supplement study.

Thirty post-menopausal women, fifteen on a combined vitamin D + calcium regime and
fifteen on vitamin D alone. Each woman had one lumbar spine scan read at four
vertebral levels (L1-L4), giving 120 vertebral-level readings in total.

Structure of the simulation:
  reading = grand mean
          + regime effect
          + woman random effect   (between-woman SD ~0.10 g/cm^2)
          + level offset          (systematic L1..L4 shape of the lumbar spine)
          + measurement noise     (within-woman SD ~0.03 g/cm^2)

Because every reading of one woman shares her woman random effect, the four
readings from a single spine resemble each other far more closely than readings
from different women, as real repeated measurements do.

Standard library only. Fixed seed, so the CSVs are reproducible byte for byte.
"""

import csv
import os
import random

SEED = 20260823
GRAND_MEAN = 0.960          # g/cm^2, vitamin D alone reference level
REGIME_EFFECT = 0.045       # g/cm^2, added for the combined regime
BETWEEN_WOMAN_SD = 0.100    # g/cm^2
WITHIN_WOMAN_SD = 0.030     # g/cm^2
LEVEL_OFFSETS = {           # g/cm^2, usual lumbar shape: density rises L1 -> L4
    "L1": -0.022,
    "L2": -0.006,
    "L3": +0.009,
    "L4": +0.019,
}
LEVELS = ["L1", "L2", "L3", "L4"]
N_PER_REGIME = 15

COMBINED = "vitamin_d_calcium"
ALONE = "vitamin_d_only"

HERE = os.path.dirname(os.path.abspath(__file__))
LEVEL_CSV = os.path.join(HERE, "vertebral_level_readings.csv")
PATIENT_CSV = os.path.join(HERE, "patient_summary.csv")


def main():
    rng = random.Random(SEED)

    refs = ["BD-%02d" % i for i in range(1, 2 * N_PER_REGIME + 1)]

    # Randomised allocation, forced to exactly fifteen women per regime.
    regimes = [COMBINED] * N_PER_REGIME + [ALONE] * N_PER_REGIME
    rng.shuffle(regimes)
    allocation = dict(zip(refs, regimes))

    level_rows = []
    summary_rows = []

    for ref in refs:
        regime = allocation[ref]
        woman_effect = rng.gauss(0.0, BETWEEN_WOMAN_SD)
        base = GRAND_MEAN + (REGIME_EFFECT if regime == COMBINED else 0.0) + woman_effect

        readings = []
        for level in LEVELS:
            value = base + LEVEL_OFFSETS[level] + rng.gauss(0.0, WITHIN_WOMAN_SD)
            value = round(value, 3)   # scanner reports three decimal places
            readings.append(value)
            level_rows.append(
                {
                    "patient_ref": ref,
                    "supplement_regime": regime,
                    "vertebral_level": level,
                    "bmd_g_per_cm2": "%.3f" % value,
                }
            )

        # The summary is derived from the rounded level readings, so the two
        # files agree with each other numerically.
        mean_bmd = sum(readings) / len(readings)
        summary_rows.append(
            {
                "patient_ref": ref,
                "supplement_regime": regime,
                "mean_bmd_g_per_cm2": "%.4f" % round(mean_bmd, 4),
                "n_levels": len(readings),
            }
        )

    with open(LEVEL_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["patient_ref", "supplement_regime", "vertebral_level", "bmd_g_per_cm2"],
        )
        writer.writeheader()
        writer.writerows(level_rows)

    with open(PATIENT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["patient_ref", "supplement_regime", "mean_bmd_g_per_cm2", "n_levels"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print("wrote %d level rows to %s" % (len(level_rows), LEVEL_CSV))
    print("wrote %d summary rows to %s" % (len(summary_rows), PATIENT_CSV))


if __name__ == "__main__":
    main()
