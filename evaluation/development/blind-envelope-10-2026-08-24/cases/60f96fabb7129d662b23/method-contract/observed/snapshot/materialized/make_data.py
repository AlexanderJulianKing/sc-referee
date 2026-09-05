"""Deterministic generator for the urban/rural red fox field dataset.

Running this script rewrites `fox_habitat_measurements.csv` in the same
directory. The generator is seeded, so repeated runs reproduce the file
byte-for-byte.

Design of the simulated field season:
  * 68 collared adult red foxes, 34 trapped inside the city and 34 in the
    surrounding farmland.
  * One row per fox, four outcomes measured once per animal.
  * Home range comes from six months of collar fixes, so it is the outcome
    with the widest spread; one rural animal dispersed out of the study area
    and carries an implausibly large home range of roughly 22 km2.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_GROUP = 34
OUT_PATH = Path(__file__).resolve().parent / "fox_habitat_measurements.csv"

COLUMNS = [
    "fox_id",
    "habitat_group",
    "body_condition_index",
    "home_range_km2",
    "faecal_cortisol_ng_per_g",
    "diet_shannon_index",
]

# Per-group population parameters (mean, sd) and the plausible measurement
# window each outcome is clipped into.
PARAMS = {
    "urban": {
        "body_condition_index": (1.03, 0.105),
        "home_range_km2": (0.95, 0.38),
        "faecal_cortisol_ng_per_g": (121.0, 33.0),
        "diet_shannon_index": (1.58, 0.30),
    },
    "rural": {
        "body_condition_index": (0.99, 0.115),
        "home_range_km2": (2.70, 1.05),
        "faecal_cortisol_ng_per_g": (95.0, 30.0),
        "diet_shannon_index": (1.50, 0.33),
    },
}

BOUNDS = {
    "body_condition_index": (0.60, 1.40),
    "home_range_km2": (0.20, 6.00),
    "faecal_cortisol_ng_per_g": (20.0, 250.0),
    "diet_shannon_index": (0.50, 2.50),
}

ROUNDING = {
    "body_condition_index": 2,
    "home_range_km2": 2,
    "faecal_cortisol_ng_per_g": 1,
    "diet_shannon_index": 2,
}

# The single dispersing rural animal that left the study area during the
# collar period.
DISPERSER_HOME_RANGE_KM2 = 22.14


def draw_group(rng: np.random.Generator, group: str) -> list[dict]:
    """Draw one habitat group's worth of fox records."""
    records: list[dict] = []
    draws = {}
    for outcome, (mean, sd) in PARAMS[group].items():
        low, high = BOUNDS[outcome]
        values = np.clip(rng.normal(mean, sd, N_PER_GROUP), low, high)
        draws[outcome] = np.round(values, ROUNDING[outcome])
    for i in range(N_PER_GROUP):
        record = {"habitat_group": group}
        for outcome in PARAMS[group]:
            record[outcome] = float(draws[outcome][i])
        records.append(record)
    return records


def build_rows() -> list[dict]:
    rng = np.random.default_rng(SEED)
    urban = draw_group(rng, "urban")
    rural = draw_group(rng, "rural")

    # One rural fox dispersed out of the study area; its collar fixes give an
    # implausibly large home range relative to every other animal.
    disperser_index = int(rng.integers(0, N_PER_GROUP))
    rural[disperser_index]["home_range_km2"] = DISPERSER_HOME_RANGE_KM2

    records = urban + rural
    # Identifiers follow trapping order, which interleaves the two areas.
    order = rng.permutation(len(records))
    rows = []
    for new_position, source_index in enumerate(order, start=1):
        record = records[source_index]
        rows.append(
            {
                "fox_id": f"FOX{new_position:03d}",
                "habitat_group": record["habitat_group"],
                "body_condition_index": f"{record['body_condition_index']:.2f}",
                "home_range_km2": f"{record['home_range_km2']:.2f}",
                "faecal_cortisol_ng_per_g": f"{record['faecal_cortisol_ng_per_g']:.1f}",
                "diet_shannon_index": f"{record['diet_shannon_index']:.2f}",
            }
        )
    return rows


def main() -> None:
    rows = build_rows()
    with OUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
