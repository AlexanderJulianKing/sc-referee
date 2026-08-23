"""Generate the synthetic ewe-level dataset for the pre-lambing mineral drench trial.

Forty-four ewes on one hill farm, twenty-two drenched and twenty-two undrenched.
Each ewe is recorded once, at weaning, and contributes exactly one row.

Run:  /usr/local/bin/python3 make_data.py
Uses only the Python standard library. Fixed seed, so the file is reproducible.
"""

import csv
import os
import random

SEED = 20260821
N_PER_GROUP = 22

TARGET_MEAN = {"drenched": 41.5, "undrenched": 37.8}
TARGET_SD = 6.5

# Effects folded into total weaned weight, in kg.
BETA_LAMBS = 4.0          # per extra lamb weaned
BETA_BCS = 2.0            # per unit of body condition score at mating
P_TWINS = 0.60            # probability a ewe weans two lambs

MEAN_LAMBS = 1.0 + P_TWINS
MEAN_BCS = 3.0

# Residual spread chosen so the total within-group spread is about TARGET_SD.
VAR_LAMBS = P_TWINS * (1.0 - P_TWINS)
VAR_BCS = 0.25
RESID_SD = (TARGET_SD ** 2 - BETA_LAMBS ** 2 * VAR_LAMBS - BETA_BCS ** 2 * VAR_BCS) ** 0.5


def draw_bcs(rng):
    """Body condition score at mating, five-point scale recorded in half units."""
    return round(min(4.5, max(1.5, rng.gauss(MEAN_BCS, 0.5))) * 2) / 2


def build_group(rng, treatment, start_index):
    rows = []
    for i in range(N_PER_GROUP):
        lambs = 2 if rng.random() < P_TWINS else 1
        age = rng.randint(2, 6)
        bcs = draw_bcs(rng)
        latent = (
            BETA_LAMBS * (lambs - MEAN_LAMBS)
            + BETA_BCS * (bcs - MEAN_BCS)
            + rng.gauss(0.0, RESID_SD)
        )
        rows.append(
            {
                "ewe_id": "E{:03d}".format(start_index + i),
                "treatment": treatment,
                "lambs_weaned": lambs,
                "ewe_age_years": age,
                "body_condition_score": bcs,
                "total_weaned_lamb_weight_kg": latent,
            }
        )

    # Re-centre the group on its target mean without changing the spread.
    realised = sum(r["total_weaned_lamb_weight_kg"] for r in rows) / len(rows)
    shift = TARGET_MEAN[treatment] - realised
    for r in rows:
        r["total_weaned_lamb_weight_kg"] = round(r["total_weaned_lamb_weight_kg"] + shift, 1)
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_group(rng, "drenched", 1) + build_group(rng, "undrenched", 101)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ewe_weaning_weights.csv")
    fields = [
        "ewe_id",
        "treatment",
        "lambs_weaned",
        "ewe_age_years",
        "body_condition_score",
        "total_weaned_lamb_weight_kg",
    ]
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
