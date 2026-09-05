"""Generate the batch-level quality dataset for the conching-temperature study.

Sixty production batches of 70 percent dark chocolate from a single cocoa origin:
thirty batches conched at 50 C and thirty conched at 65 C, each sampled once after
a fixed tempering and resting schedule. Five quality outcomes are measured once per
batch.

Deterministic: fixed seed, no external inputs. Running this file rewrites
chocolate_batches.csv byte-for-byte.
"""

import csv
import os

import numpy as np

SEED = 20260824
N_PER_GROUP = 30
GROUPS = ("conche_50c", "conche_65c")

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chocolate_batches.csv")

# Per-group generating means and within-group standard deviations for each outcome.
# Some outcomes carry a modest process difference between conching temperatures;
# others are generated from the same distribution in both groups.
OUTCOME_SPEC = {
    # name: (mean_50c, mean_65c, sd, decimals, plausible min, plausible max)
    "particle_d90_um": (23.6, 22.4, 1.55, 1, 18.0, 28.0),
    "hardness_n": (52.4, 51.6, 6.40, 1, 35.0, 70.0),
    "melt_peak_c": (32.88, 32.94, 0.42, 2, 31.5, 34.5),
    "gloss_gu": (96.0, 103.5, 12.0, 1, 60.0, 140.0),
    "bitterness_score": (4.95, 4.30, 0.72, 1, 2.5, 6.5),
}

COLUMNS = [
    "batch_id",
    "conche_group",
    "particle_d90_um",
    "hardness_n",
    "melt_peak_c",
    "gloss_gu",
    "bitterness_score",
]


def build_rows(rng):
    """Return one dict per production batch, in batch-number order."""
    # Production ran the two conching temperatures in alternating blocks of five
    # batches, so the group labels are interleaved across the batch sequence.
    group_labels = []
    for block in range(N_PER_GROUP * 2 // 5):
        group_labels.extend([GROUPS[block % 2]] * 5)

    # A batch-level tempering-quality latent: well-tempered batches show slightly
    # higher gloss and a slightly higher melting peak. It is shared by both groups
    # and so does not create a group difference on its own.
    temper_quality = rng.normal(0.0, 1.0, size=len(group_labels))

    rows = []
    for idx, group in enumerate(group_labels):
        row = {
            "batch_id": "B{:03d}".format(idx + 1),
            "conche_group": group,
        }
        for name, (mean_50, mean_65, sd, decimals, lo, hi) in OUTCOME_SPEC.items():
            mean = mean_50 if group == GROUPS[0] else mean_65
            value = rng.normal(mean, sd)
            if name == "gloss_gu":
                value += 4.5 * temper_quality[idx]
            elif name == "melt_peak_c":
                value += 0.16 * temper_quality[idx]
            value = float(np.clip(value, lo, hi))
            row[name] = format(round(value, decimals), ".{}f".format(decimals))
        rows.append(row)
    return rows


def main():
    rng = np.random.default_rng(SEED)
    rows = build_rows(rng)
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
