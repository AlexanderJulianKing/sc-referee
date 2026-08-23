"""Generate zebrafish_activity.csv for the fluoxetine novel-tank study.

Design: 8 tanks (4 control, 4 fluoxetine), 12 fish per tank, 96 fish in total.
Fluoxetine was dosed into the tank water, so the exposure sits at the tank
level. Each tank therefore gets its own baseline activity level (water
chemistry, position on the rack, social make-up of the group), and individual
fish are scattered around their own tank's baseline. The spread of the tank
baselines is set larger than the average difference between the two exposure
conditions.

Distances and body lengths are drawn from separate random streams so that one
does not shift the other. Seeds are fixed, so the file is reproducible.
"""

import csv
import numpy as np

SEED = 20260830
rng_distance = np.random.default_rng(SEED)
rng_body = np.random.default_rng(SEED + 1)

N_TANKS = 8
FISH_PER_TANK = 12

GRAND_MEAN_CM = 1300.0       # typical control distance over the 6-minute trial
TREATMENT_SHIFT_CM = -160.0  # fluoxetine fish move somewhat less
TANK_SD_CM = 175.0           # between-tank spread, larger than the shift above
FISH_SD_CM = 115.0           # fish-to-fish spread within a tank

BODY_MEAN_MM = 36.0
BODY_SD_MM = 1.4
BODY_MIN_MM, BODY_MAX_MM = 31.0, 41.0  # safety rail only; the draw stays inside it

# Whole tanks are assigned to a condition.
tank_ids = [f"TNK-{i:02d}" for i in range(1, N_TANKS + 1)]
exposures = ["control"] * 4 + ["fluoxetine"] * 4

# Tank baselines, then fish deviations around their own tank baseline.
tank_offsets = rng_distance.normal(0.0, TANK_SD_CM, size=N_TANKS)
fish_noise = rng_distance.normal(0.0, FISH_SD_CM, size=(N_TANKS, FISH_PER_TANK))

body_lengths = np.clip(
    rng_body.normal(BODY_MEAN_MM, BODY_SD_MM, size=(N_TANKS, FISH_PER_TANK)),
    BODY_MIN_MM,
    BODY_MAX_MM,
)

rows = []
for i, (tank_id, exposure) in enumerate(zip(tank_ids, exposures)):
    shift = TREATMENT_SHIFT_CM if exposure == "fluoxetine" else 0.0
    tank_level = GRAND_MEAN_CM + shift + tank_offsets[i]
    for j in range(FISH_PER_TANK):
        rows.append({
            "aquarium_ref": tank_id,
            "exposure": exposure,
            "fish_label": f"F{j + 1:02d}",
            "body_length_mm": round(float(body_lengths[i, j]), 1),
            "distance_cm": round(float(tank_level + fish_noise[i, j]), 1),
        })

out_path = "zebrafish_activity.csv"
with open(out_path, "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=[
        "aquarium_ref", "exposure", "fish_label", "body_length_mm", "distance_cm",
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {out_path} with {len(rows)} rows")
