"""Generate the earthworm body-mass dataset for the biochar mesocosm study.

Standard library only. Fixed seed so the CSV is reproducible byte-for-byte.

Design generated here:
  * 12 independent soil mesocosms (MES01 .. MES12)
  * 6 mesocosms amended with biochar, 6 unamended controls
  * 10 earthworms weighed per mesocosm at week 8  -> 120 rows total

Value model:
  body_mass_mg = treatment mean + mesocosm offset + worm-level scatter
      control treatment mean  = 420 mg
      biochar treatment mean  = 470 mg
      mesocosm offset  ~ Normal(0, 25 mg)   (container-to-container differences)
      worm scatter     ~ Normal(0, 55 mg)   (worm-to-worm within a container)
  soil_moisture_pct: one value per mesocosm, drawn 22-30 %, repeated on the
      10 rows belonging to that mesocosm.
  gut_cleared: per-worm yes/no, about 85 % yes.
"""

import csv
import os
import random

SEED = 20260823
N_MESOCOSMS = 12
WORMS_PER_MESOCOSM = 10

TREATMENT_MEAN_MG = {"control": 420.0, "biochar": 470.0}
MESOCOSM_SD_MG = 25.0
WORM_SD_MG = 55.0

MASS_MIN_MG = 300.0
MASS_MAX_MG = 620.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "earthworm_body_mass.csv")

COLUMNS = [
    "mesocosm_id",
    "treatment",
    "worm_id",
    "body_mass_mg",
    "gut_cleared",
    "soil_moisture_pct",
]


def main():
    rng = random.Random(SEED)

    # Randomly assign 6 mesocosms to each treatment, so treatment is not
    # confounded with mesocosm numbering order.
    mesocosm_ids = ["MES%02d" % i for i in range(1, N_MESOCOSMS + 1)]
    assignment = ["control"] * 6 + ["biochar"] * 6
    rng.shuffle(assignment)
    treatment_of = dict(zip(mesocosm_ids, assignment))

    rows = []
    for mesocosm_id in mesocosm_ids:
        treatment = treatment_of[mesocosm_id]
        mesocosm_offset = rng.gauss(0.0, MESOCOSM_SD_MG)
        soil_moisture_pct = round(rng.uniform(22.0, 30.0), 1)

        for worm_index in range(1, WORMS_PER_MESOCOSM + 1):
            mass = TREATMENT_MEAN_MG[treatment] + mesocosm_offset + rng.gauss(0.0, WORM_SD_MG)
            mass = min(max(mass, MASS_MIN_MG), MASS_MAX_MG)
            rows.append(
                {
                    "mesocosm_id": mesocosm_id,
                    "treatment": treatment,
                    "worm_id": "%s-W%02d" % (mesocosm_id, worm_index),
                    "body_mass_mg": "%.1f" % mass,
                    "gut_cleared": "yes" if rng.random() < 0.85 else "no",
                    "soil_moisture_pct": "%.1f" % soil_moisture_pct,
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_PATH, len(rows)))


if __name__ == "__main__":
    main()
