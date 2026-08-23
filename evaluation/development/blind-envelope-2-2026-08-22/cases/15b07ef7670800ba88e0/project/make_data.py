"""Generate the raw pup-level dataset for the maternal protein-restriction study.

Design
------
16 dams, one litter each: 8 dams on the control diet, 8 dams on the
protein-restricted diet. Every litter was culled to 8 pups on postnatal day 2
and all of those pups were weighed on postnatal day 21, giving 128 weighed
pups in total.

Generating model for pup body mass on day 21 (grams):

    mass_ij = group_mean(diet_i) + litter_effect_i + pup_noise_ij

    litter_effect_i ~ Normal(0, 3.5)   between-litter SD
    pup_noise_ij    ~ Normal(0, 2.5)   within-litter (littermate) SD

    group_mean(control)            = 52.0 g
    group_mean(protein_restricted) = 45.0 g

Masses are rounded to one decimal place. Sex is assigned within each litter as
4 females and 4 males, shuffled, and has no effect on the simulated mass.

Seed selection (disclosed for transparency)
------------------------------------------
Seeds were scanned upward from 20260822 and the first one kept whose *realized*
variance components landed near the values the study design specifies: a
between-litter SD of the eight litter means inside [2.8, 4.3] g and a mean
within-litter SD inside [2.1, 2.9] g, in BOTH diet groups. Seed 20260827 was
the first to pass.

That screen looks only at spread. It never inspects the group means, their
difference, or any test statistic, and it is arithmetically blind to them,
because the group mean is added after the random draws and shifts every pup in
a group by the same constant. It does, however, condition on the between-litter
spread, so the litter means in this file are slightly less dispersed than a
wholly unconditioned draw would be. Anyone re-deriving sampling properties from
this generator should account for that.

Run with: /usr/local/bin/python3 make_data.py
Only the Python standard library is used.
"""

import csv
import os
import random

SEED = 20260827

N_LITTERS_PER_GROUP = 8
N_PUPS_PER_LITTER = 8

GROUP_MEAN = {"control": 52.0, "protein_restricted": 45.0}
BETWEEN_LITTER_SD = 3.5
WITHIN_LITTER_SD = 2.5

HERE = os.path.dirname(os.path.abspath(__file__))
PUPS_CSV = os.path.join(HERE, "pup_masses.csv")


def main():
    rng = random.Random(SEED)

    # Litters L01..L16; the first 8 are control dams, the last 8 are
    # protein-restricted dams.
    litters = []
    for index in range(N_LITTERS_PER_GROUP * 2):
        diet = "control" if index < N_LITTERS_PER_GROUP else "protein_restricted"
        litters.append(("L%02d" % (index + 1), diet))

    rows = []
    for litter_id, diet in litters:
        litter_effect = rng.gauss(0.0, BETWEEN_LITTER_SD)
        sexes = ["F"] * (N_PUPS_PER_LITTER // 2) + ["M"] * (N_PUPS_PER_LITTER // 2)
        rng.shuffle(sexes)
        for pup_index in range(N_PUPS_PER_LITTER):
            mass = GROUP_MEAN[diet] + litter_effect + rng.gauss(0.0, WITHIN_LITTER_SD)
            rows.append(
                {
                    "litter_id": litter_id,
                    "diet_group": diet,
                    "pup_id": "%s-P%d" % (litter_id, pup_index + 1),
                    "sex": sexes[pup_index],
                    "body_mass_g": round(mass, 1),
                }
            )

    with open(PUPS_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["litter_id", "diet_group", "pup_id", "sex", "body_mass_g"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d pup rows to %s" % (len(rows), PUPS_CSV))


if __name__ == "__main__":
    main()
