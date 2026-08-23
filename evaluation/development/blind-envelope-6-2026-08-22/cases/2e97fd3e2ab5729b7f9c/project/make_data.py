"""Generate the raw blade-measurement CSV for the sugar kelp seeding-density trial.

Standard library only. Fixed seed so the file regenerates byte-for-byte.

Design that this generator mirrors:
  * 14 dropper lines from one longline, 7 seeded at standard density and
    7 seeded at reduced density.
  * 10 haphazardly selected blades measured per dropper line after 5 months.
  * Blade length is drawn as line mean + blade deviation, so blades on the
    same line are correlated (the line, not the blade, is the independent unit).
  * Blade wet mass tracks blade length with modest extra scatter.
"""

import csv
import os
import random

SEED = 20260822

N_LINES_PER_DENSITY = 7
N_BLADES_PER_LINE = 10

# Length model (cm)
MEAN_STANDARD = 96.0        # grand mean, standard seeding density
MEAN_REDUCED = 118.0        # grand mean, reduced seeding density
SD_BETWEEN_LINES = 15.0     # line-to-line variation in line mean length
SD_WITHIN_LINE = 22.0       # blade-to-blade variation inside one line

# Wet mass model (g): mass tracks length
MASS_PER_CM = 2.4           # g of wet mass per cm of blade length
MASS_INTERCEPT = 5.0        # g
SD_MASS_RESIDUAL = 18.0     # g of scatter not explained by length

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kelp_blades.csv")

FIELDNAMES = [
    "dropper_line",
    "seeding_density",
    "blade_number",
    "blade_length_cm",
    "blade_wet_mass_g",
]


def main():
    rng = random.Random(SEED)

    lines = []
    for i in range(N_LINES_PER_DENSITY):
        lines.append(("L%02d" % (i + 1), "standard", MEAN_STANDARD))
    for i in range(N_LINES_PER_DENSITY):
        lines.append(("L%02d" % (i + 1 + N_LINES_PER_DENSITY), "reduced", MEAN_REDUCED))

    rows = []
    for line_id, density, grand_mean in lines:
        line_mean = grand_mean + rng.gauss(0.0, SD_BETWEEN_LINES)
        for blade in range(1, N_BLADES_PER_LINE + 1):
            length = line_mean + rng.gauss(0.0, SD_WITHIN_LINE)
            if length < 15.0:
                length = 15.0
            mass = MASS_INTERCEPT + MASS_PER_CM * length + rng.gauss(0.0, SD_MASS_RESIDUAL)
            if mass < 5.0:
                mass = 5.0
            rows.append(
                {
                    "dropper_line": line_id,
                    "seeding_density": density,
                    "blade_number": blade,
                    "blade_length_cm": "%.1f" % length,
                    "blade_wet_mass_g": "%.1f" % mass,
                }
            )

    with open(OUT_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows, %d dropper lines)"
          % (OUT_PATH, len(rows), len(lines)))


if __name__ == "__main__":
    main()
