"""Generate the winter wheat fungicide programme trial data set.

Deterministic: a fixed seed drives every random draw, so re-running this script
reproduces wheat_fungicide_trial.csv byte for byte.

Trial layout
------------
One site, 144 individually tagged winter wheat plants, 72 under each fungicide
programme (single_spray = one spray at flag leaf emergence, two_spray = an
earlier stem extension spray added). Independently of programme, the plants were
allocated in advance to a discovery half and a validation half, 72 plants each,
balanced so that every half holds 36 plants from each programme. That allocation
is drawn here once and written into the stage_split column.

Plant-level structure
---------------------
Each plant carries a latent vigour term (soil, tillering, establishment) and a
latent disease pressure term (canopy microclimate, inoculum arriving on that
plant). Outcomes are built from those two terms plus programme effects, so the
six measurements are correlated within a plant the way field measurements are:
vigorous plants are taller, carry more spikes and yield more; heavily diseased
plants lose green canopy and yield; plants with many spikes have slightly
lighter individual grains.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_PROGRAM = 72
N_PER_PROGRAM_PER_HALF = 36
OUT_PATH = Path(__file__).resolve().parent / "wheat_fungicide_trial.csv"

COLUMNS = [
    "plant_id",
    "program_group",
    "stage_split",
    "grain_yield_g",
    "tgw_g",
    "septoria_severity_pct",
    "green_canopy_days",
    "plant_height_cm",
    "spike_count",
]

# Programme shifts. Positive = the two-spray programme scores higher on the raw
# scale of that outcome. Height and spike number carry no programme shift beyond
# the trivial value below; yield, thousand grain weight, septoria severity and
# green canopy duration do.
SEPTORIA_MEAN = {"single_spray": 27.0, "two_spray": 15.5}
CANOPY_MEAN = {"single_spray": 30.0, "two_spray": 32.2}
YIELD_SHIFT = {"single_spray": 0.0, "two_spray": 1.5}
TGW_SHIFT = {"single_spray": 0.0, "two_spray": 1.0}
HEIGHT_SHIFT = {"single_spray": 0.0, "two_spray": 0.3}
SPIKE_SHIFT = {"single_spray": 0.0, "two_spray": 0.05}


def assign_split(rng: np.random.Generator) -> list[str]:
    """Pre-registered allocation: 36 discovery and 36 validation per programme."""
    labels = ["discovery"] * N_PER_PROGRAM_PER_HALF + ["validation"] * N_PER_PROGRAM_PER_HALF
    labels = np.array(labels, dtype=object)
    rng.shuffle(labels)
    return list(labels)


def simulate_program(rng: np.random.Generator, program: str) -> dict[str, np.ndarray]:
    n = N_PER_PROGRAM

    vigour = rng.normal(0.0, 1.0, n)
    disease_pressure = rng.normal(0.0, 1.0, n)

    septoria = (
        SEPTORIA_MEAN[program]
        + 7.0 * disease_pressure
        - 1.1 * vigour
        + rng.normal(0.0, 4.0, n)
    )
    septoria = np.clip(septoria, 0.4, 59.5)

    canopy = (
        CANOPY_MEAN[program]
        - 0.15 * (septoria - 21.0)
        + 1.2 * vigour
        + rng.normal(0.0, 3.0, n)
    )
    canopy = np.clip(canopy, 18.2, 44.8)

    height = 82.0 + HEIGHT_SHIFT[program] + 4.5 * vigour + rng.normal(0.0, 4.0, n)
    height = np.clip(height, 65.5, 99.5)

    spikes = 4.7 + SPIKE_SHIFT[program] + 0.75 * vigour + rng.normal(0.0, 0.7, n)
    spikes = np.clip(np.rint(spikes), 2, 8)

    yield_g = (
        15.5
        + YIELD_SHIFT[program]
        + 1.5 * vigour
        + 0.85 * (spikes - 4.7)
        - 0.055 * (septoria - 21.0)
        + 0.12 * (canopy - 31.0)
        + rng.normal(0.0, 1.6, n)
    )
    yield_g = np.clip(yield_g, 8.1, 27.9)

    tgw = (
        42.0
        + TGW_SHIFT[program]
        + 0.9 * vigour
        - 0.5 * (spikes - 4.7)
        - 0.05 * (septoria - 21.0)
        + rng.normal(0.0, 2.4, n)
    )
    tgw = np.clip(tgw, 32.2, 51.8)

    return {
        "grain_yield_g": np.round(yield_g, 2),
        "tgw_g": np.round(tgw, 1),
        "septoria_severity_pct": np.round(septoria, 1),
        "green_canopy_days": np.round(canopy, 1),
        "plant_height_cm": np.round(height, 1),
        "spike_count": spikes.astype(int),
    }


def build_rows() -> list[dict[str, object]]:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    plant_no = 0

    for program in ("single_spray", "two_spray"):
        outcomes = simulate_program(rng, program)
        splits = assign_split(rng)
        for i in range(N_PER_PROGRAM):
            plant_no += 1
            row: dict[str, object] = {
                "plant_id": f"WW-{plant_no:03d}",
                "program_group": program,
                "stage_split": splits[i],
            }
            for name, values in outcomes.items():
                row[name] = values[i]
            rows.append(row)

    # Tagged plants are recorded in field walking order, which mixes programmes.
    order = np.random.default_rng(SEED + 1).permutation(len(rows))
    shuffled = [rows[i] for i in order]
    for new_no, row in enumerate(shuffled, start=1):
        row["plant_id"] = f"WW-{new_no:03d}"
    return shuffled


def main() -> None:
    rows = build_rows()
    with OUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "plant_id": row["plant_id"],
                    "program_group": row["program_group"],
                    "stage_split": row["stage_split"],
                    "grain_yield_g": f"{row['grain_yield_g']:.2f}",
                    "tgw_g": f"{row['tgw_g']:.1f}",
                    "septoria_severity_pct": f"{row['septoria_severity_pct']:.1f}",
                    "green_canopy_days": f"{row['green_canopy_days']:.1f}",
                    "plant_height_cm": f"{row['plant_height_cm']:.1f}",
                    "spike_count": int(row["spike_count"]),
                }
            )
    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
