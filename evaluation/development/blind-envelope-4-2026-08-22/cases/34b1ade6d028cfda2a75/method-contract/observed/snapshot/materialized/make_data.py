"""Generate the marram grass dune survey data set.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design: 10 dunes along one stretch of coast, 5 fenced against rabbits for three
years and 5 unfenced. Six 1 m quadrats per dune, placed along a fixed line from
the seaward toe to the crest. One row per quadrat, 60 rows in total.

Values: fenced group mean 48 % cover, unfenced group mean 31 % cover, a
whole-dune offset with SD 7 percentage points (exposure and sand supply), and
quadrat-to-quadrat variation within a dune with SD 9 percentage points. Cover is
rounded to a whole number and clamped to the 0-100 range.
"""

import csv
import os
import random

SEED = 20260829

FENCED_MEAN = 48.0
UNFENCED_MEAN = 31.0
DUNE_SD = 7.0
QUADRAT_SD = 9.0
QUADRATS_PER_DUNE = 6

# Ten plausible short dune names, one per dune.
DUNES = [
    ("Braid Hollow", "fenced"),
    ("Corrie Links", "unfenced"),
    ("Sandhaven", "fenced"),
    ("Kelpie Bank", "unfenced"),
    ("Nether Ness", "fenced"),
    ("Whin Head", "unfenced"),
    ("Salt Pans", "fenced"),
    ("Tern Bar", "unfenced"),
    ("Reddings", "fenced"),
    ("Gull Rigg", "unfenced"),
]

OUT_NAME = "marram_cover.csv"
COLUMNS = ["dune_name", "rabbit_exclusion", "quadrat_number", "marram_cover_pct"]


def main():
    rng = random.Random(SEED)
    rows = []

    for dune_name, treatment in DUNES:
        group_mean = FENCED_MEAN if treatment == "fenced" else UNFENCED_MEAN
        dune_offset = rng.gauss(0.0, DUNE_SD)
        dune_mean = group_mean + dune_offset

        for quadrat_number in range(1, QUADRATS_PER_DUNE + 1):
            cover = dune_mean + rng.gauss(0.0, QUADRAT_SD)
            cover = int(round(cover))
            cover = max(0, min(100, cover))
            rows.append([dune_name, treatment, quadrat_number, cover])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    print("wrote {} data rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
