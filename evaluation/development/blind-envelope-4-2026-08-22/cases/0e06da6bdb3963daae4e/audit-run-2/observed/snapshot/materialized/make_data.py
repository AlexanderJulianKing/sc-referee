"""Generate the hatchery carapace-length dataset for the sea turtle substrate study.

Standard library only. Fixed seed so the CSV is reproducible.

Design mirrored by the generator:
  * 24 relocated green turtle clutches, 12 per substrate.
  * A clutch-level random effect (between-clutch SD 1.8 mm) shared by all
    hatchlings from the same mother's clutch.
  * A hatchling-level residual (within-clutch SD 1.2 mm) around that clutch mean.
  * Substrate means: native 43.6 mm, imported 41.2 mm.
  * Values rounded to 0.1 mm and kept inside 36.0-49.0 mm by redrawing the few
    residuals that would land outside the believable range.
"""

import csv
import os
import random

SEED = 20260822

N_CLUTCHES = 24
CLUTCHES_PER_SUBSTRATE = 12
HATCHLINGS_PER_CLUTCH = 10

SUBSTRATE_MEAN_MM = {"native": 43.6, "imported": 41.2}
BETWEEN_CLUTCH_SD_MM = 1.8
WITHIN_CLUTCH_SD_MM = 1.2

MIN_LENGTH_MM = 36.0
MAX_LENGTH_MM = 49.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hatchling_carapace.csv")


def draw_in_range(rng, mean_mm, sd_mm):
    """Draw a normal value, redrawing until it sits inside the plausible range."""
    for _ in range(1000):
        value = rng.gauss(mean_mm, sd_mm)
        if MIN_LENGTH_MM <= value <= MAX_LENGTH_MM:
            return value
    raise RuntimeError("could not draw a value inside the plausible range")


def build_rows():
    rng = random.Random(SEED)

    # Assign substrates to clutch numbers in a fixed shuffled order so that the
    # two groups are interleaved rather than blocked by clutch number.
    substrates = ["native"] * CLUTCHES_PER_SUBSTRATE + ["imported"] * CLUTCHES_PER_SUBSTRATE
    rng.shuffle(substrates)

    rows = []
    for index in range(N_CLUTCHES):
        clutch_ref = "CL-%02d" % (index + 1)
        substrate = substrates[index]
        clutch_mean = SUBSTRATE_MEAN_MM[substrate] + rng.gauss(0.0, BETWEEN_CLUTCH_SD_MM)
        # Keep the clutch mean itself well inside the range so that hatchling
        # draws are only rarely rejected.
        clutch_mean = min(max(clutch_mean, MIN_LENGTH_MM + 2.0), MAX_LENGTH_MM - 2.0)
        for hatchling_number in range(1, HATCHLINGS_PER_CLUTCH + 1):
            length_mm = draw_in_range(rng, clutch_mean, WITHIN_CLUTCH_SD_MM)
            rows.append(
                {
                    "clutch_ref": clutch_ref,
                    "substrate": substrate,
                    "hatchling_number": hatchling_number,
                    "carapace_length_mm": "%.1f" % length_mm,
                }
            )
    return rows


def main():
    rows = build_rows()
    fieldnames = ["clutch_ref", "substrate", "hatchling_number", "carapace_length_mm"]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %d data rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
