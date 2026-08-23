"""Generate the alpaca fleece trial dataset.

Twenty adult huacaya alpacas, ten on a trace-mineral supplemented ration and ten
on the unsupplemented ration, each sampled once a month for four consecutive
months. Standard library only; fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260847
N_ANIMALS = 20
N_MONTHS = 4
MONTHS = ["2026-03", "2026-04", "2026-05", "2026-06"]

# Group-level fleece diameter targets (micrometres).
GROUP_MEAN_UM = {"unsupplemented": 26.5, "supplemented": 24.5}
# Persistent between-animal spread and month-to-month within-animal spread.
BETWEEN_ANIMAL_SD_UM = 1.8
WITHIN_ANIMAL_SD_UM = 0.8
# Plausible measurement range for the instrument/flock.
DIAMETER_MIN_UM, DIAMETER_MAX_UM = 19.0, 31.0


def main():
    rng = random.Random(SEED)

    # Alternate group assignment so both arms are balanced at ten animals.
    animals = []
    for i in range(1, N_ANIMALS + 1):
        alpaca_id = "ALP%02d" % i
        diet_group = "supplemented" if i % 2 == 0 else "unsupplemented"
        animal_offset = rng.gauss(0.0, BETWEEN_ANIMAL_SD_UM)
        age_years = rng.randint(2, 11)
        # Older animals sit a little heavier; start weight drawn around that.
        start_weight = rng.gauss(62.0 + 1.6 * age_years, 4.5)
        start_weight = min(max(start_weight, 55.0), 82.0)
        animals.append(
            {
                "alpaca_id": alpaca_id,
                "diet_group": diet_group,
                "animal_offset": animal_offset,
                "age_years": age_years,
                "start_weight": start_weight,
            }
        )

    rows = []
    for a in animals:
        base = GROUP_MEAN_UM[a["diet_group"]] + a["animal_offset"]
        weight = a["start_weight"]
        for m, month in enumerate(MONTHS):
            diameter = base + rng.gauss(0.0, WITHIN_ANIMAL_SD_UM)
            diameter = min(max(diameter, DIAMETER_MIN_UM), DIAMETER_MAX_UM)
            # Weight drifts slowly month to month within a plausible band.
            if m > 0:
                weight = weight + rng.gauss(0.6, 1.2)
            weight = min(max(weight, 55.0), 85.0)
            rows.append(
                {
                    "alpaca_id": a["alpaca_id"],
                    "diet_group": a["diet_group"],
                    "sampling_month": month,
                    "fibre_diameter_um": round(diameter, 2),
                    "age_years": a["age_years"],
                    "body_weight_kg": round(weight, 1),
                }
            )

    rows.sort(key=lambda r: (r["alpaca_id"], r["sampling_month"]))

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "alpaca_fibre.csv")
    fieldnames = [
        "alpaca_id",
        "diet_group",
        "sampling_month",
        "fibre_diameter_um",
        "age_years",
        "body_weight_kg",
    ]
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
