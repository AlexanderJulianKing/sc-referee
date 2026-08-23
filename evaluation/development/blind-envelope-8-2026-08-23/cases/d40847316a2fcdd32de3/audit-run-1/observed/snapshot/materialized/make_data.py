"""Generate the termite-mound soil nitrogen data set.

Standard library only. Fixed seed, so re-running reproduces the CSV byte for byte.

Design encoded here:
  * 14 large termite mounds are the independent units.
  * 7 mounds sit in a block burned two years earlier, 7 in an adjacent unburned block.
  * 8 soil cores per mound -> 112 rows, one row per core.
  * Cores from the same mound are spatial subsamples and are therefore correlated:
    each mound carries its own offset that every one of its cores shares.
"""

import csv
import os
import random

SEED = 20260823
N_MOUNDS = 14
N_CORES_PER_MOUND = 8

# Nitrogen model, percent by mass.
UNBURNED_MEAN_PCT = 0.21     # cores from unburned-block mounds average near this
BURNED_MEAN_PCT = 0.15       # cores from burned-block mounds average near this
BETWEEN_MOUND_SD_PCT = 0.040  # pronounced mound-to-mound differences
WITHIN_MOUND_SD_PCT = 0.025   # core-to-core variation inside one mound
N_MIN_PCT, N_MAX_PCT = 0.04, 0.38

# With only seven mounds per block, an unconstrained draw of the mound offsets can
# land the realised block means far from the values the study description asks for.
# The seven offsets in a block are therefore redrawn until the block mean sits close
# to its target and the offsets still spread out across mounds.
BLOCK_MEAN_TOLERANCE_PCT = 0.010
MIN_BETWEEN_MOUND_SD_PCT = 0.025
MAX_DRAW_ATTEMPTS = 100000

DEPTH_CHOICES_CM = [10, 20, 30]

OUT_NAME = "termite_mound_soil_nitrogen.csv"


def clamp(value, low, high):
    return max(low, min(high, value))


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def draw_block_mound_means(rng, target_mean, n_mounds):
    """Draw per-mound nitrogen means for one block.

    Keeps redrawing the whole block until the mean of the mounds is within
    BLOCK_MEAN_TOLERANCE_PCT of the target and the mound-to-mound spread is at
    least MIN_BETWEEN_MOUND_SD_PCT.
    """
    for _ in range(MAX_DRAW_ATTEMPTS):
        means = [
            target_mean + rng.gauss(0.0, BETWEEN_MOUND_SD_PCT) for _ in range(n_mounds)
        ]
        if abs(mean(means) - target_mean) > BLOCK_MEAN_TOLERANCE_PCT:
            continue
        if sample_sd(means) < MIN_BETWEEN_MOUND_SD_PCT:
            continue
        return means
    raise RuntimeError("could not draw a block meeting the spread and mean conditions")


def main():
    rng = random.Random(SEED)

    # Mounds 1-7 sit in the unburned block, mounds 8-14 in the burned block.
    half = N_MOUNDS // 2
    block_means = {
        "unburned": draw_block_mound_means(rng, UNBURNED_MEAN_PCT, half),
        "burned": draw_block_mound_means(rng, BURNED_MEAN_PCT, half),
    }

    mounds = []
    for i in range(1, N_MOUNDS + 1):
        burn_block = "unburned" if i <= half else "burned"
        position = i - 1 if burn_block == "unburned" else i - 1 - half
        mounds.append(
            {
                "mound_id": "MND%02d" % i,
                "burn_block": burn_block,
                # shared level for every core on this mound
                "mound_nitrogen_mean_pct": block_means[burn_block][position],
                "mound_height_m": round(rng.uniform(0.8, 3.5), 2),
                # mound-level soil reaction; mound soils run mildly alkaline
                "mound_ph_mean": rng.gauss(7.4, 0.35),
            }
        )

    rows = []
    for mound in mounds:
        for core in range(1, N_CORES_PER_MOUND + 1):
            nitrogen = mound["mound_nitrogen_mean_pct"] + rng.gauss(
                0.0, WITHIN_MOUND_SD_PCT
            )
            nitrogen = clamp(nitrogen, N_MIN_PCT, N_MAX_PCT)

            ph = mound["mound_ph_mean"] + rng.gauss(0.0, 0.18)
            ph = clamp(ph, 5.8, 8.6)

            rows.append(
                {
                    "mound_id": mound["mound_id"],
                    "burn_block": mound["burn_block"],
                    "core_number": core,
                    "total_nitrogen_pct": round(nitrogen, 3),
                    "mound_height_m": mound["mound_height_m"],
                    "core_distance_cm": round(rng.uniform(20.0, 150.0), 1),
                    "sample_depth_cm": rng.choice(DEPTH_CHOICES_CM),
                    "soil_ph": round(ph, 2),
                }
            )

    fields = [
        "mound_id",
        "burn_block",
        "core_number",
        "total_nitrogen_pct",
        "mound_height_m",
        "core_distance_cm",
        "sample_depth_cm",
        "soil_ph",
    ]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows, %d mounds)" % (OUT_NAME, len(rows), N_MOUNDS))


if __name__ == "__main__":
    main()
