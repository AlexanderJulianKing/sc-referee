"""Generate the hemp harvest-timing dataset used as the analysis input.

Deterministic: a fixed seed drives every random draw, so re-running this script
reproduces hemp_harvest_timing.csv byte for byte.

Scenario: 96 individually tagged dual-purpose industrial hemp plants of one
cultivar on one field site, 48 harvested at early flowering and 48 harvested at
seed maturity. Each plant is measured once after retting and decortication.

Values are simulated with plant-level vigour shared across the size-related
outcomes, so bast fibre yield and stem diameter co-vary the way they do in a
real stand. Draws are clipped to the agronomically plausible ranges stated in
the protocol.
"""

import csv
import os

import numpy as np

SEED = 20260824
N_PER_GROUP = 48
GROUPS = ("early_flower", "seed_mature")

OUTFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "hemp_harvest_timing.csv")

# Per-group generating parameters.
#   key -> (mean_early, sd_early, mean_seed, sd_seed, lo, hi, vigour_loading)
# vigour_loading is how strongly the shared plant vigour factor moves the trait.
PARAMS = {
    "bast_fibre_yield_g": (49.0, 9.5, 56.5, 11.0, 20.0, 90.0, 7.5),
    "tensile_strength_mpa": (655.0, 85.0, 545.0, 92.0, 300.0, 900.0, 25.0),
    "stem_diameter_mm": (9.6, 1.7, 10.2, 1.9, 5.0, 16.0, 1.3),
    "cbd_pct_dry": (1.32, 0.34, 1.24, 0.36, 0.4, 2.5, 0.10),
    "stem_moisture_pct": (19.4, 2.4, 12.9, 2.3, 8.0, 25.0, 0.55),
}

ROUNDING = {
    "bast_fibre_yield_g": 1,
    "tensile_strength_mpa": 0,
    "stem_diameter_mm": 1,
    "cbd_pct_dry": 2,
    "stem_moisture_pct": 1,
}


def main():
    rng = np.random.default_rng(SEED)

    rows = []
    plant_counter = 0
    for group_index, group in enumerate(GROUPS):
        # Shared plant-level vigour: standardised, one value per plant.
        vigour = rng.normal(0.0, 1.0, N_PER_GROUP)

        columns = {}
        for name, (m_e, s_e, m_s, s_s, lo, hi, load) in PARAMS.items():
            mean, sd = (m_e, s_e) if group_index == 0 else (m_s, s_s)
            # Split the variance between shared vigour and trait-specific noise.
            resid_sd = max(sd ** 2 - load ** 2, 0.01) ** 0.5
            values = mean + load * vigour + rng.normal(0.0, resid_sd, N_PER_GROUP)
            values = np.clip(values, lo, hi)
            columns[name] = np.round(values, ROUNDING[name])

        for i in range(N_PER_GROUP):
            plant_counter += 1
            row = {
                "plant_id": "HMP-{:03d}".format(plant_counter),
                "harvest_group": group,
            }
            for name in PARAMS:
                value = float(columns[name][i])
                row[name] = ("{:.0f}".format(value) if ROUNDING[name] == 0
                             else "{:.{}f}".format(value, ROUNDING[name]))
            rows.append(row)

    fieldnames = ["plant_id", "harvest_group"] + list(PARAMS)
    with open(OUTFILE, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUTFILE))


if __name__ == "__main__":
    main()
