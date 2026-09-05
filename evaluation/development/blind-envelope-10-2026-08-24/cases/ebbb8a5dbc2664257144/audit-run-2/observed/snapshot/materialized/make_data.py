"""Deterministic generator for the turnout-coat thermal liner heat-strain dataset.

Creates heat_strain.csv: one row per firefighter, 44 firefighters, 22 wearing the
current service-issue liner and 22 wearing the candidate lighter liner, with the
four declared heat-strain outcomes measured once each during a single
standardised live-fire training evolution.

Run:
    python make_data.py

The generator is seeded, so the CSV is byte-for-byte reproducible.
"""

from __future__ import annotations

import csv
import pathlib

import numpy as np

SEED = 20260824
N_PER_GROUP = 22
OUT_PATH = pathlib.Path(__file__).resolve().parent / "heat_strain.csv"

# Outcome order follows the protocol's declared order.
OUTCOMES = [
    "peak_core_temp_c",
    "peak_heart_rate_bpm",
    "sweat_loss_l",
    "exhaustion_time_min",
]

# Target within-group location and spread for each outcome, chosen to sit inside
# the physiological ranges seen in structural-firefighting burn-building work.
# Group means differ modestly on some outcomes and barely at all on others.
TARGETS = {
    "liner_current": {
        "peak_core_temp_c": (38.92, 0.30),
        "peak_heart_rate_bpm": (182.4, 8.2),
        "sweat_loss_l": (1.14, 0.24),
        "exhaustion_time_min": (19.4, 3.9),
    },
    "liner_candidate": {
        "peak_core_temp_c": (38.64, 0.28),
        "peak_heart_rate_bpm": (176.6, 8.0),
        "sweat_loss_l": (1.07, 0.22),
        "exhaustion_time_min": (21.6, 4.1),
    },
}

# Rounding applied to each recorded value, matching how the monitoring kit logs it.
DECIMALS = {
    "peak_core_temp_c": 2,
    "peak_heart_rate_bpm": 0,
    "sweat_loss_l": 2,
    "exhaustion_time_min": 1,
}

# A firefighter who runs hot tends to run hot on every strain measure, and the
# hotter they run the sooner they stop, so exhaustion time is anti-correlated
# with the other three. Order matches OUTCOMES.
CORRELATION = np.array(
    [
        [1.00, 0.52, 0.44, -0.46],
        [0.52, 1.00, 0.38, -0.40],
        [0.44, 0.38, 1.00, -0.33],
        [-0.46, -0.40, -0.33, 1.00],
    ]
)

TRUNCATION = 1.9  # keeps individual draws inside plausible physiological bounds


def draw_latent(rng: np.random.Generator, n: int) -> np.ndarray:
    """Draw n correlated standard-normal rows, redrawing any extreme row."""
    chol = np.linalg.cholesky(CORRELATION)
    rows = []
    while len(rows) < n:
        row = chol @ rng.standard_normal(len(OUTCOMES))
        if np.all(np.abs(row) <= TRUNCATION):
            rows.append(row)
    return np.array(rows)


def shape(values: np.ndarray, mean: float, sd: float) -> np.ndarray:
    """Rescale a column so its sample mean and sample sd hit the targets."""
    centred = values - values.mean()
    scaled = centred / centred.std(ddof=1)
    return mean + sd * scaled


BOUNDS = {
    "peak_core_temp_c": (38.0, 39.5),
    "peak_heart_rate_bpm": (160, 198),
    "sweat_loss_l": (0.5, 1.7),
    "exhaustion_time_min": (12.0, 30.0),
}


def build_group(rng: np.random.Generator, group: str) -> dict[str, np.ndarray]:
    """Draw one group's block, redrawing until every recorded value is in range."""
    while True:
        latent = draw_latent(rng, N_PER_GROUP)
        block: dict[str, np.ndarray] = {}
        for j, outcome in enumerate(OUTCOMES):
            mean, sd = TARGETS[group][outcome]
            shaped = shape(latent[:, j], mean, sd)
            block[outcome] = np.round(shaped, DECIMALS[outcome])
        low_high = [BOUNDS[o] for o in OUTCOMES]
        if all(
            lo <= block[o].min() and block[o].max() <= hi
            for o, (lo, hi) in zip(OUTCOMES, low_high)
        ):
            return block


def build() -> list[dict[str, object]]:
    rng = np.random.default_rng(SEED)

    columns: dict[str, dict[str, np.ndarray]] = {}
    for group in ("liner_current", "liner_candidate"):
        columns[group] = build_group(rng, group)

    # Assignment order on the roster: alternating, as the crews were paired off
    # before the evolution.
    assignment = ["liner_current", "liner_candidate"] * N_PER_GROUP
    cursor = {"liner_current": 0, "liner_candidate": 0}

    rows: list[dict[str, object]] = []
    for i, group in enumerate(assignment, start=1):
        k = cursor[group]
        cursor[group] += 1
        row: dict[str, object] = {
            "firefighter_id": f"FF-{i:02d}",
            "liner_group": group,
        }
        for outcome in OUTCOMES:
            value = columns[group][outcome][k]
            row[outcome] = int(value) if DECIMALS[outcome] == 0 else float(value)
        rows.append(row)
    return rows


def check(rows: list[dict[str, object]]) -> None:
    """Fail loudly if any recorded value leaves its plausible measurement range."""
    for row in rows:
        for outcome, (low, high) in BOUNDS.items():
            value = row[outcome]
            if not low <= value <= high:
                raise ValueError(f"{row['firefighter_id']} {outcome}={value} out of range")
    if len(rows) != 2 * N_PER_GROUP:
        raise ValueError("unexpected row count")


def write(rows: list[dict[str, object]]) -> None:
    header = ["firefighter_id", "liner_group", *OUTCOMES]
    with OUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in header})


def main() -> None:
    rows = build()
    check(rows)
    write(rows)
    print(f"wrote {OUT_PATH} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
