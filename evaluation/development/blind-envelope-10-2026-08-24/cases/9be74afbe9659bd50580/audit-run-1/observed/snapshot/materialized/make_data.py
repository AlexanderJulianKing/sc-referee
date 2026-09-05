"""Deterministic generator for the cold plasma almond decontamination dataset.

Simulates sixty almond lots from a single harvest, thirty treated with cold
plasma for two minutes and thirty for five minutes at the same power setting,
each lot measured once on five outcomes after four weeks of ambient storage.

Running this file rewrites almond_plasma_lots.csv next to it. The random seed is
fixed, so the same CSV is produced on every run.

This script only builds the dataset. It performs no comparison of the two
treatment groups.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_GROUP = 30

OUT_PATH = Path(__file__).resolve().parent / "almond_plasma_lots.csv"

COLUMNS = [
    "lot_id",
    "plasma_group",
    "surrogate_log_reduction",
    "peroxide_value_meq_kg",
    "colour_l_star",
    "moisture_pct",
    "rancid_odour_score",
]

# Per-group generating parameters (mean, standard deviation) and the plausible
# instrument range each measurement is clipped to.
PARAMS = {
    "surrogate_log_reduction": {
        "plasma_2min": (1.62, 0.34),
        "plasma_5min": (2.38, 0.41),
        "range": (0.5, 3.5),
        "decimals": 2,
    },
    "peroxide_value_meq_kg": {
        "plasma_2min": (1.48, 0.42),
        "plasma_5min": (2.06, 0.49),
        "range": (0.5, 4.0),
        "decimals": 2,
    },
    "colour_l_star": {
        "plasma_2min": (56.4, 2.10),
        "plasma_5min": (55.8, 2.25),
        "range": (48.0, 62.0),
        "decimals": 1,
    },
    "moisture_pct": {
        "plasma_2min": (4.82, 0.38),
        "plasma_5min": (4.71, 0.41),
        "range": (3.5, 6.0),
        "decimals": 2,
    },
    "rancid_odour_score": {
        "plasma_2min": (1.45, 0.68),
        "plasma_5min": (1.92, 0.79),
        "range": (0.0, 5.0),
        "decimals": 1,
    },
}


def build_rows() -> list[dict[str, object]]:
    rng = np.random.default_rng(SEED)

    n_total = 2 * N_PER_GROUP
    lot_ids = [f"LOT-{i:03d}" for i in range(1, n_total + 1)]

    # Randomised allocation: the treatment order is shuffled across lot numbers
    # rather than assigned in blocks.
    groups = np.array(["plasma_2min"] * N_PER_GROUP + ["plasma_5min"] * N_PER_GROUP)
    rng.shuffle(groups)

    # Latent per-lot oxidation susceptibility, shared by peroxide value and
    # rancid odour so that the two lipid-oxidation readouts move together, and
    # weakly tied to residual moisture in the opposite direction.
    oxidation = rng.normal(0.0, 1.0, size=n_total)

    values: dict[str, np.ndarray] = {}
    for column, spec in PARAMS.items():
        means = np.array([spec[g][0] for g in groups])
        sds = np.array([spec[g][1] for g in groups])
        noise = rng.normal(0.0, 1.0, size=n_total)

        if column == "peroxide_value_meq_kg":
            draw = means + sds * (0.72 * oxidation + 0.69 * noise)
        elif column == "rancid_odour_score":
            draw = means + sds * (0.58 * oxidation + 0.81 * noise)
        elif column == "moisture_pct":
            draw = means + sds * (-0.25 * oxidation + 0.97 * noise)
        else:
            draw = means + sds * noise

        low, high = spec["range"]
        draw = np.clip(draw, low, high)
        values[column] = np.round(draw, spec["decimals"])

    rows: list[dict[str, object]] = []
    for i in range(n_total):
        row: dict[str, object] = {"lot_id": lot_ids[i], "plasma_group": str(groups[i])}
        for column, spec in PARAMS.items():
            value = float(values[column][i])
            row[column] = f"{value:.{spec['decimals']}f}"
        rows.append(row)
    return rows


def main() -> None:
    rows = build_rows()
    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} lots to {OUT_PATH.name}")


if __name__ == "__main__":
    main()
