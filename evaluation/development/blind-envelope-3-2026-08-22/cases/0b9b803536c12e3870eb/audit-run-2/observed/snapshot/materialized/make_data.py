"""Generate the simulated grip-strength data file for the two-programme study.

Twenty-six volunteers (13 heavy, 13 moderate) each performed four maximal
handgrip trials in a single testing session, so the file holds 104 rows.

Between-volunteer spread is set to about 7 kg and within-volunteer trial-to-trial
spread to about 1.8 kg, with a small downward drift across the four trials to
represent fatigue. Standard library only; no third-party packages required.
"""

import csv
import os
import random

SEED = 20260867

N_PER_GROUP = 13
N_TRIALS = 4

GROUP_MEANS = {"heavy": 44.5, "moderate": 41.0}
BETWEEN_SD = 7.0          # kg, spread between volunteers
WITHIN_SD = 1.8           # kg, spread among one volunteer's four trials
FATIGUE_PER_TRIAL = 0.35  # kg lost per trial after the first

# Body mass is generated separately, by sex, in kilograms.
BODY_MASS = {"female": (66.0, 8.5), "male": (79.0, 9.5)}

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grip_strength.csv")


def main() -> None:
    rng = random.Random(SEED)
    rows = []

    for programme in ("heavy", "moderate"):
        prefix = "H" if programme == "heavy" else "M"
        for i in range(1, N_PER_GROUP + 1):
            volunteer_id = f"{prefix}{i:02d}"
            # Alternate sex within each group so the two groups are comparable.
            sex = "female" if i % 2 == 0 else "male"

            mass_mean, mass_sd = BODY_MASS[sex]
            body_mass_kg = round(rng.gauss(mass_mean, mass_sd), 1)

            # One true level per volunteer, drawn around the programme mean.
            volunteer_true = rng.gauss(GROUP_MEANS[programme], BETWEEN_SD)

            for trial_number in range(1, N_TRIALS + 1):
                drift = -FATIGUE_PER_TRIAL * (trial_number - 1)
                peak = volunteer_true + drift + rng.gauss(0.0, WITHIN_SD)
                rows.append(
                    {
                        "volunteer_id": volunteer_id,
                        "programme": programme,
                        "trial_number": trial_number,
                        "peak_force_kg": round(peak, 1),
                        "sex": sex,
                        "body_mass_kg": body_mass_kg,
                    }
                )

    fieldnames = [
        "volunteer_id",
        "programme",
        "trial_number",
        "peak_force_kg",
        "sex",
        "body_mass_kg",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
