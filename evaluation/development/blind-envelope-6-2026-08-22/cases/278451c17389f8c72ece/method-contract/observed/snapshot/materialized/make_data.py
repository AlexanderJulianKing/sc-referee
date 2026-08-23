"""Generate the harvest record for the butterhead lettuce nutrient trial.

Ten nutrient-film gutters, five on the standard formulation and five on the
raised-potassium formulation. Twelve plant positions are cut and weighed in
every gutter, giving 120 harvested heads in total.

Standard library only. Fixed seed so the CSV is reproducible.
"""

import csv
import os
import random

SEED = 20260806

# Head fresh mass targets (g)
MEAN_STANDARD = 245.0
MEAN_RAISED_K = 278.0

SD_BETWEEN_GUTTERS = 25.0   # gutter-to-gutter spread (g)
SD_WITHIN_GUTTER = 30.0     # head-to-head spread inside one gutter (g)

# Nutrient depletion along the channel: heads further from the dosing end run
# lighter. Centred on the middle of the gutter so the formulation means are
# not shifted by the gradient.
GRADIENT_G_PER_POSITION = -1.4
CENTRE_POSITION = 6.5

POSITIONS = 12
GUTTERS_PER_FORMULATION = 5

# Harvest was done over two mornings; gutters 1-5 on the first day,
# gutters 6-10 on the second.
HARVEST_DATES = {1: "2026-06-15", 2: "2026-06-16"}

COLUMNS = [
    "gutter_code",
    "formulation",
    "position_along_gutter",
    "head_fresh_mass_g",
    "harvest_date",
]


def build_rows():
    rng = random.Random(SEED)

    # Gutters are laid out alternating across the glasshouse so that the two
    # formulations are interleaved rather than banked at one end.
    layout = []
    for block in range(GUTTERS_PER_FORMULATION):
        layout.append("standard")
        layout.append("raised_potassium")

    rows = []
    for index, formulation in enumerate(layout, start=1):
        gutter_code = "G{:02d}".format(index)
        base = MEAN_STANDARD if formulation == "standard" else MEAN_RAISED_K
        gutter_offset = rng.gauss(0.0, SD_BETWEEN_GUTTERS)
        harvest_date = HARVEST_DATES[1 if index <= 5 else 2]

        for position in range(1, POSITIONS + 1):
            gradient = GRADIENT_G_PER_POSITION * (position - CENTRE_POSITION)
            mass = base + gutter_offset + gradient + rng.gauss(0.0, SD_WITHIN_GUTTER)
            rows.append(
                {
                    "gutter_code": gutter_code,
                    "formulation": formulation,
                    "position_along_gutter": position,
                    "head_fresh_mass_g": round(mass, 1),
                    "harvest_date": harvest_date,
                }
            )
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "lettuce_harvest.csv")
    rows = build_rows()
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
