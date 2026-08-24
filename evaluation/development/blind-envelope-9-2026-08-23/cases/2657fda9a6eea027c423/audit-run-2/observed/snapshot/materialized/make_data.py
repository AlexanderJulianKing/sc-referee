"""Generate the ergometer trial data for the rowing training-block study.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.
The seed was chosen from a scan of candidate seeds so that the realised data match
the magnitudes the study specifies (about a 15 W group difference, values inside
the 225-335 W band); the generating model itself is unchanged by that choice.

Structure of the simulated measurements:
  * 18 club rowers, 9 in the interval block and 9 in the endurance block
  * each rower performs 4 maximal 500 m trials on 4 separate days
  * a rower's own level is drawn around the group mean (between-rower SD ~30 W)
  * each trial varies around that rower's own level (within-rower SD ~8 W)
"""

import csv
import random

SEED = 20260217
N_ROWERS = 18
N_TRIALS = 4

GROUP_MEANS_W = {"interval": 287.5, "endurance": 272.5}
BETWEEN_ROWER_SD_W = 27.0
WITHIN_ROWER_SD_W = 8.0

OUTPUT_CSV = "erg_trials.csv"


def build_rows():
    rng = random.Random(SEED)

    rower_ids = ["R%02d" % i for i in range(1, N_ROWERS + 1)]

    # Randomised allocation: nine rowers to each six-week block.
    allocation = ["interval"] * 9 + ["endurance"] * 9
    rng.shuffle(allocation)
    block_of = dict(zip(rower_ids, allocation))

    rows = []
    for rower_id in rower_ids:
        block = block_of[rower_id]
        rower_level_w = rng.gauss(GROUP_MEANS_W[block], BETWEEN_ROWER_SD_W)
        for trial in range(1, N_TRIALS + 1):
            power_w = rng.gauss(rower_level_w, WITHIN_ROWER_SD_W)
            rows.append(
                {
                    "rower_id": rower_id,
                    "training_block": block,
                    "trial_number": trial,
                    "mean_power_w": round(power_w, 1),
                }
            )
    return rows


def main():
    rows = build_rows()
    fieldnames = ["rower_id", "training_block", "trial_number", "mean_power_w"]
    with open(OUTPUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    powers = [r["mean_power_w"] for r in rows]
    print("rows written:", len(rows))
    print("min / max watts:", min(powers), max(powers))
    for block in ("interval", "endurance"):
        vals = [r["mean_power_w"] for r in rows if r["training_block"] == block]
        n_rowers = len({r["rower_id"] for r in rows if r["training_block"] == block})
        print(block, "rowers:", n_rowers, "rows:", len(vals),
              "mean:", round(sum(vals) / len(vals), 2))


if __name__ == "__main__":
    main()
