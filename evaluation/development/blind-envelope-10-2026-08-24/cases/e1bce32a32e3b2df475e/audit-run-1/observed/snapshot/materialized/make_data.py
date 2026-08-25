"""Generate the picker-level measurement file for the exoskeleton picking-round study.

Deterministic: the script is seeded, so re-running it reproduces exo_picking_trial.csv
byte for byte.

Run:
    python make_data.py

One hundred order pickers, fifty wearing a passive back-support exoskeleton and fifty
working the same shift pattern without one. Each picker is measured once on a
standardised mixed-case picking round, giving one row per picker and one column per
declared outcome.

Structure of the generated values
---------------------------------
Each picker carries a latent "strain susceptibility" score. Pickers who load their spine
harder on the round also tend to rate the round as harder work and to finish the shift
with more shoulder discomfort, so the three strain-related outcomes share part of that
latent score instead of being drawn independently. Round time and picking errors are
driven mainly by pace and attention, so they are only weakly tied to strain.

Group-to-group offsets are set per outcome. Peak lumbar compression carries the largest
offset, perceived exertion a smaller one, shoulder discomfort a small offset in the
opposite direction (the harness loads the shoulders), and round time and picking errors
are given offsets close to zero.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_GROUP = 50
OUTPUT = Path(__file__).resolve().parent / "exo_picking_trial.csv"

COLUMNS = [
    "picker_id",
    "exo_group",
    "peak_lumbar_compression_n",
    "borg_exertion_score",
    "round_time_min",
    "picking_errors",
    "shoulder_discomfort_score",
]

# Per-outcome population settings.
#   centre : control-group mean
#   spread : within-group standard deviation
#   offset : exoskeleton-group mean minus control-group mean
#   rho    : share of the picker's latent strain score carried by this outcome
LUMBAR = dict(centre=3910.0, spread=520.0, offset=-455.0, rho=0.55)
BORG = dict(centre=14.1, spread=2.05, offset=-1.30, rho=0.50)
ROUND_TIME = dict(centre=29.8, spread=4.9, offset=0.45, rho=0.25)
SHOULDER = dict(centre=3.5, spread=1.80, offset=1.05, rho=0.45)

# Picking errors are counts, modelled as Poisson draws around a per-picker rate.
ERROR_RATE_CONTROL = 2.55
ERROR_RATE_EXO = 2.70
ERROR_RATE_STRAIN_WEIGHT = 0.22

# Instrument / instrument-panel limits used to clip stray draws.
LUMBAR_LIMITS = (2000.0, 5500.0)
BORG_LIMITS = (8, 19)
ROUND_TIME_LIMITS = (18.0, 45.0)
ERROR_LIMITS = (0, 8)
SHOULDER_LIMITS = (0, 9)


def latent_mix(rng, latent, spread, rho, n):
    """Draw a mean-zero deviation of size `spread` sharing `rho` of the latent score."""
    independent = rng.standard_normal(n)
    return spread * (rho * latent + np.sqrt(1.0 - rho**2) * independent)


def build():
    rng = np.random.default_rng(SEED)
    n = 2 * N_PER_GROUP

    # Group labels: fifty of each, then shuffled across the picker roster so that the
    # identifier order carries no information about assignment.
    group = np.array(["control"] * N_PER_GROUP + ["exoskeleton"] * N_PER_GROUP)
    rng.shuffle(group)
    is_exo = group == "exoskeleton"

    latent = rng.standard_normal(n)

    lumbar = (
        LUMBAR["centre"]
        + is_exo * LUMBAR["offset"]
        + latent_mix(rng, latent, LUMBAR["spread"], LUMBAR["rho"], n)
    )
    borg = (
        BORG["centre"]
        + is_exo * BORG["offset"]
        + latent_mix(rng, latent, BORG["spread"], BORG["rho"], n)
    )
    round_time = (
        ROUND_TIME["centre"]
        + is_exo * ROUND_TIME["offset"]
        + latent_mix(rng, latent, ROUND_TIME["spread"], ROUND_TIME["rho"], n)
    )
    shoulder = (
        SHOULDER["centre"]
        + is_exo * SHOULDER["offset"]
        + latent_mix(rng, latent, SHOULDER["spread"], SHOULDER["rho"], n)
    )

    error_rate = np.where(is_exo, ERROR_RATE_EXO, ERROR_RATE_CONTROL) * np.exp(
        ERROR_RATE_STRAIN_WEIGHT * latent
    )
    errors = rng.poisson(error_rate)

    # Apply the recording resolution of each instrument, then clip to its stated range.
    lumbar = np.clip(np.round(lumbar), *LUMBAR_LIMITS).astype(int)
    borg = np.clip(np.round(borg), *BORG_LIMITS).astype(int)
    round_time = np.clip(np.round(round_time, 1), *ROUND_TIME_LIMITS)
    errors = np.clip(errors, *ERROR_LIMITS).astype(int)
    shoulder = np.clip(np.round(shoulder), *SHOULDER_LIMITS).astype(int)

    rows = []
    for i in range(n):
        rows.append(
            {
                "picker_id": f"P{i + 1:03d}",
                "exo_group": group[i],
                "peak_lumbar_compression_n": int(lumbar[i]),
                "borg_exertion_score": int(borg[i]),
                "round_time_min": f"{round_time[i]:.1f}",
                "picking_errors": int(errors[i]),
                "shoulder_discomfort_score": int(shoulder[i]),
            }
        )
    return rows


def main():
    rows = build()
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUTPUT.name}")


if __name__ == "__main__":
    main()
