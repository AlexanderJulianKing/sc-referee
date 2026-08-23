"""Generate the experimental-evolution growth-rate dataset.

Sixteen independent lineages (eight evolved under a sub-inhibitory efflux-pump
inhibitor, eight evolved in plain medium) were each assayed six times on the
same frozen stock on the same plate reader, giving 96 rows.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260823
N_LINEAGES_PER_REGIME = 8
N_RUNS_PER_LINEAGE = 6

REGIME_MEAN = {
    "inhibitor": 0.56,   # per hour
    "plain": 0.71,       # per hour
}
BETWEEN_LINEAGE_SD = 0.045   # real differences between lineages within a regime
TECHNICAL_SD = 0.030         # scatter between assay runs on one frozen stock

GROWTH_MIN, GROWTH_MAX = 0.40, 0.90

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(OUT_DIR, "growth_rates.csv")

COLUMNS = [
    "lineage_id",
    "selection_regime",
    "replicate_run",
    "growth_rate_per_h",
    "plate_id",
    "well",
    "final_od600",
]


def clamp(value, low, high):
    return max(low, min(high, value))


def well_names():
    """48 well positions: rows A-D, columns 1-12, zero-padded column."""
    return ["%s%02d" % (row, col) for row in "ABCD" for col in range(1, 13)]


def main():
    rng = random.Random(SEED)

    # LIN01-LIN08 evolved with the inhibitor, LIN09-LIN16 in plain medium.
    lineages = []
    for i in range(1, N_LINEAGES_PER_REGIME + 1):
        lineages.append(("LIN%02d" % i, "inhibitor"))
    for i in range(N_LINEAGES_PER_REGIME + 1, 2 * N_LINEAGES_PER_REGIME + 1):
        lineages.append(("LIN%02d" % i, "plain"))

    # Each lineage's own true growth rate, drawn around its regime mean.
    lineage_true = {}
    for lineage_id, regime in lineages:
        mean = rng.gauss(REGIME_MEAN[regime], BETWEEN_LINEAGE_SD)
        lineage_true[lineage_id] = clamp(mean, GROWTH_MIN + 0.04, GROWTH_MAX - 0.04)

    # Both regimes are split across the two plates so plate is not confounded
    # with selection regime. All six runs of a lineage sit on one plate.
    plate_of = {}
    for lineage_id, _ in lineages:
        index = int(lineage_id[3:])
        block = (index - 1) % 8
        plate_of[lineage_id] = "PLT01" if block < 4 else "PLT02"

    # Randomised well layout within each plate.
    free_wells = {}
    for plate in ("PLT01", "PLT02"):
        wells = well_names()
        rng.shuffle(wells)
        free_wells[plate] = wells

    rows = []
    for lineage_id, regime in lineages:
        plate = plate_of[lineage_id]
        for run in range(1, N_RUNS_PER_LINEAGE + 1):
            growth = clamp(
                rng.gauss(lineage_true[lineage_id], TECHNICAL_SD),
                GROWTH_MIN,
                GROWTH_MAX,
            )
            od = clamp(0.95 + 0.60 * (growth - 0.63) + rng.gauss(0.0, 0.045), 0.55, 1.60)
            rows.append({
                "lineage_id": lineage_id,
                "selection_regime": regime,
                "replicate_run": run,
                "growth_rate_per_h": round(growth, 4),
                "plate_id": plate,
                "well": free_wells[plate].pop(),
                "final_od600": round(od, 3),
            })

    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
