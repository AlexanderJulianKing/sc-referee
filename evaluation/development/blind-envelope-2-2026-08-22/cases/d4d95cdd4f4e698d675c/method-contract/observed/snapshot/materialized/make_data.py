"""Generate the organoid barrier-function dataset.

One row per measured well: 18 donors (9 risk-variant carriers, 9 non-carriers),
6 wells per donor, 108 wells in total.

Structure built into the numbers:
  * genotype is a fixed property of the donor, so all 6 wells of a donor share it
  * donor level = group mean + donor random effect (between-donor SD ~45)
  * well value  = donor level + well noise (within-donor SD ~30)
  * non-carrier wells average ~412 ohm-cm^2, carrier wells ~318 ohm-cm^2

Standard library only. Fixed seed, so the CSV reproduces exactly.
Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260132

MEAN_NONCARRIER = 412.0   # ohm-cm^2, day-7 TEER, non-carrier donors
MEAN_CARRIER = 318.0      # ohm-cm^2, day-7 TEER, carrier donors
SD_BETWEEN_DONOR = 45.0   # donor-to-donor spread around the group mean
SD_WITHIN_DONOR = 30.0    # well-to-well spread around a donor's own level

N_DONORS_PER_GROUP = 9
WELL_POSITIONS = ["A1", "A2", "A3", "B1", "B2", "B3"]  # same layout for every donor

OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "organoid_teer.csv")


def main():
    rng = random.Random(SEED)

    # Donor 1..18. Genotype is assigned to the donor, never to the well.
    # Donors D01-D09 are non-carriers, D10-D18 are carriers.
    donors = []
    for i in range(1, 2 * N_DONORS_PER_GROUP + 1):
        donor_id = "D%02d" % i
        if i <= N_DONORS_PER_GROUP:
            genotype = "non_carrier"
            group_mean = MEAN_NONCARRIER
        else:
            genotype = "carrier"
            group_mean = MEAN_CARRIER
        donors.append(
            {
                "donor_id": donor_id,
                "genotype": genotype,
                # one preparation per donor -> one passage number per donor
                "passage_number": rng.randint(2, 5),
                "donor_age_years": rng.randint(24, 68),
                # the donor's own true barrier level
                "donor_level": group_mean + rng.gauss(0.0, SD_BETWEEN_DONOR),
            }
        )

    rows = []
    for donor in donors:
        for position in WELL_POSITIONS:
            teer = donor["donor_level"] + rng.gauss(0.0, SD_WITHIN_DONOR)
            rows.append(
                {
                    "donor_id": donor["donor_id"],
                    "genotype": donor["genotype"],
                    "well_position": position,
                    "passage_number": donor["passage_number"],
                    "donor_age_years": donor["donor_age_years"],
                    "teer_day7_ohm_cm2": round(teer, 1),
                }
            )

    fieldnames = [
        "donor_id",
        "genotype",
        "well_position",
        "passage_number",
        "donor_age_years",
        "teer_day7_ohm_cm2",
    ]
    with open(OUT_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (OUT_CSV, len(rows)))


if __name__ == "__main__":
    main()
