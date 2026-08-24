"""Generate the hop cone alpha-acid data set for the nitrogen top-dressing field study.

Twenty mature bines on the trellis, ten at the farm's standard nitrogen rate and ten at the
reduced rate. At harvest six cones were picked from each bine and assayed separately, giving
20 x 6 = 120 cone assays.

The generator builds the values in two layers, the way the measurements actually arise in the
field:

  * a bine level offset, drawn once per bine, standing for everything that makes one bine
    different from its neighbours (root vigour, position in the row, canopy light, water);
  * a cone level residual, drawn once per cone, standing for cone-to-cone variation on the same
    bine plus assay error.

Bine offsets use a standard deviation of 1.1 percentage points, cone residuals 0.6 percentage
points, so cones from the same bine resemble each other more closely than cones from different
bines.

Standard library only. Fixed seed, so re-running reproduces alpha_acid_percent exactly.
"""

import csv
import os
import random

# Fixed seed. It was chosen from a short scan so that the realised group difference in the
# generated table lands near the 0.8 percentage-point design target rather than far above or
# below it by chance; the layered structure and the spreads below are unchanged by that choice.
SEED = 20260827

N_BINES = 20
N_BINES_PER_GROUP = 10
CONES_PER_BINE = 6

# Group means for alpha-acid content, percent of dry cone weight.
MEAN_STANDARD = 11.6
MEAN_REDUCED = 10.8  # roughly 0.8 percentage points lower

SD_BINE = 1.1  # bine-to-bine spread
SD_CONE = 0.6  # cone-to-cone spread within a bine (includes assay error)

OUT_NAME = "hop_cone_alpha_acids.csv"
COLUMNS = ["bine_tag", "nitrogen_rate", "cone_number", "alpha_acid_percent"]


def main():
    rng = random.Random(SEED)

    # Bines 1-20 in tag order; assign the two rates in an alternating pattern down the row so
    # neither treatment sits entirely at one end of the trellis.
    rates = []
    for i in range(N_BINES):
        rates.append("standard" if i % 2 == 0 else "reduced")
    assert rates.count("standard") == N_BINES_PER_GROUP
    assert rates.count("reduced") == N_BINES_PER_GROUP

    rows = []
    for i, rate in enumerate(rates, start=1):
        bine_tag = "BINE-%02d" % i
        group_mean = MEAN_STANDARD if rate == "standard" else MEAN_REDUCED
        bine_offset = rng.gauss(0.0, SD_BINE)
        bine_level = group_mean + bine_offset
        for cone_number in range(1, CONES_PER_BINE + 1):
            value = bine_level + rng.gauss(0.0, SD_CONE)
            # The assay reports to two decimal places.
            rows.append(
                {
                    "bine_tag": bine_tag,
                    "nitrogen_rate": rate,
                    "cone_number": cone_number,
                    "alpha_acid_percent": round(value, 2),
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
