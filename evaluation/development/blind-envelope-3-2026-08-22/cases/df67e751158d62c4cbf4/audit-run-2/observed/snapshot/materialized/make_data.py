"""Generate the eggshell quality dataset for the limestone vs oyster-shell calcium trial.

Eighteen floor pens of laying hens, nine per calcium source. Twelve hens were caught at
random from each pen at the end of the trial and one freshly laid egg per sampled hen was
measured, giving 18 x 12 = 216 measured eggs.

Values are invented. Run with a fixed seed so the file is reproducible:
    python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822

N_PENS_PER_DIET = 9
N_HENS_PER_PEN = 12

# Shell thickness (mm)
DIET_MEAN_MM = {"limestone": 0.355, "oyster_shell": 0.372}
PEN_SD_MM = 0.010     # pen-to-pen spread
HEN_SD_MM = 0.018     # hen-to-hen spread inside a pen

# Egg weight (g)
EGG_WEIGHT_MEAN_G = 62.0
EGG_WEIGHT_PEN_SD_G = 1.2
EGG_WEIGHT_HEN_SD_G = 3.2

OUTFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eggshell_quality.csv")


def main():
    rng = random.Random(SEED)
    rows = []

    pen_number = 1
    for diet in ("limestone", "oyster_shell"):
        for _ in range(N_PENS_PER_DIET):
            pen_id = "P{:02d}".format(pen_number)
            pen_effect_mm = rng.gauss(0.0, PEN_SD_MM)
            pen_effect_g = rng.gauss(0.0, EGG_WEIGHT_PEN_SD_G)

            for hen in range(1, N_HENS_PER_PEN + 1):
                hen_id = "{}-H{:02d}".format(pen_id, hen)
                thickness = DIET_MEAN_MM[diet] + pen_effect_mm + rng.gauss(0.0, HEN_SD_MM)
                weight = EGG_WEIGHT_MEAN_G + pen_effect_g + rng.gauss(0.0, EGG_WEIGHT_HEN_SD_G)
                rows.append(
                    {
                        "pen_id": pen_id,
                        "diet": diet,
                        "hen_id": hen_id,
                        "shell_thickness_mm": round(thickness, 4),
                        "egg_weight_g": round(weight, 2),
                    }
                )
            pen_number += 1

    fieldnames = ["pen_id", "diet", "hen_id", "shell_thickness_mm", "egg_weight_g"]
    with open(OUTFILE, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUTFILE))


if __name__ == "__main__":
    main()
