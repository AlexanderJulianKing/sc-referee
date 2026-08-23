"""Generate the seed-potato storage-atmosphere dataset.

Postharvest trial: 14 sealed storage bins filled from one graded lot, 7 held under
conventional cold air and 7 under a low-oxygen controlled atmosphere. Every bin is
opened and sampled at six storage times (weeks 4, 8, 12, 16, 20, 24), giving
14 x 6 = 84 records.

Standard library only. Fixed seed, so the file is reproducible.
Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822
WEEKS = [4, 8, 12, 16, 20, 24]
OUT_NAME = "storage_firmness.csv"

# Bin labels in the style of the store's own tags: house-row-bin.
BIN_CODES = [
    "CS1-A01", "CS1-A02", "CS1-A03", "CS1-A04", "CS1-A05", "CS1-A06", "CS1-A07",
    "CS2-B01", "CS2-B02", "CS2-B03", "CS2-B04", "CS2-B05", "CS2-B06", "CS2-B07",
]

# Group-level firmness trend, newtons.
#   week 4 intercept -> week 24 endpoint
FIRMNESS = {
    # atmosphere: (intercept at week 4, decline per week)
    "conventional_air": (66.0, -1.10),   # ~66 N at week 4 -> ~44 N at week 24
    "low_oxygen_ca":    (67.0, -0.65),   # ~67 N at week 4 -> ~54 N at week 24
}

# Group-level weight-loss trend, percent of loading weight.
#   base at week 4 plus a per-week rise
WEIGHT_LOSS = {
    "conventional_air": (0.68, 0.330),   # ~0.68% at week 4 -> ~7.3% at week 24
    "low_oxygen_ca":    (0.70, 0.212),   # ~0.70% at week 4 -> ~4.9% at week 24
}

BIN_FIRMNESS_SD = 1.8   # each bin sits consistently above or below its group trend
FIRMNESS_NOISE_SD = 1.0  # penetrometer / sampling variation at a single visit
BIN_SLOPE_SD = 0.028     # bin-to-bin spread in weight-loss rate
WEIGHT_NOISE_SD = 0.06   # scale variation at a single visit


def build_rows(rng):
    """Assign bins to atmospheres and simulate every bin visit."""
    codes = list(BIN_CODES)
    rng.shuffle(codes)
    assignment = [(code, "conventional_air") for code in codes[:7]]
    assignment += [(code, "low_oxygen_ca") for code in codes[7:]]
    # Report in tag order so the file reads like the store's own log.
    assignment.sort(key=lambda pair: pair[0])

    rows = []
    for code, atmosphere in assignment:
        f_intercept, f_slope = FIRMNESS[atmosphere]
        w_base, w_slope = WEIGHT_LOSS[atmosphere]

        bin_firmness_offset = rng.gauss(0.0, BIN_FIRMNESS_SD)
        bin_weight_offset = rng.gauss(0.0, 0.12)
        bin_weight_slope = w_slope + rng.gauss(0.0, BIN_SLOPE_SD)

        last_loss = 0.0
        for week in WEEKS:
            elapsed = week - WEEKS[0]

            firmness = (
                f_intercept
                + f_slope * elapsed
                + bin_firmness_offset
                + rng.gauss(0.0, FIRMNESS_NOISE_SD)
            )

            loss = (
                w_base
                + bin_weight_offset
                + bin_weight_slope * elapsed
                + rng.gauss(0.0, WEIGHT_NOISE_SD)
            )
            # Weight loss since loading cannot go backwards.
            loss = max(loss, last_loss + 0.05)
            last_loss = loss

            rows.append(
                {
                    "bin_code": code,
                    "atmosphere": atmosphere,
                    "storage_week": week,
                    "weight_loss_pct": round(loss, 2),
                    "firmness_newton": round(firmness, 1),
                }
            )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fields = [
        "bin_code",
        "atmosphere",
        "storage_week",
        "weight_loss_pct",
        "firmness_newton",
    ]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d records to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
