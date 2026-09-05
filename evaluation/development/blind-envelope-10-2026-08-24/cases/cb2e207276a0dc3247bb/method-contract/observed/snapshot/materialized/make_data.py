"""Generate the sorghum nitrogen-rate field sample used by this project.

Deterministic: a fixed seed drives every random draw, so re-running this script
reproduces sorghum_nitrogen_plants.csv byte for byte.

Simulated design
----------------
One uniform field site, two nitrogen fertiliser rates (60 and 120 kg N/ha),
36 individually tagged plants sampled per rate at physiological maturity.
Four agronomic outcomes are measured once on each harvested plant.

Each plant carries a latent "vigour" term shared by all four outcomes, which
gives the outcomes the mild positive correlation seen in real plant samples
(a vigorous plant tends to be taller, carry a longer panicle and set more
grain). Measurement noise is added independently on top of that.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_GROUP = 36

OUT_PATH = Path(__file__).resolve().parent / "sorghum_nitrogen_plants.csv"

# Per-group population settings for each outcome.
# (mean, measurement sd, vigour loading, lower plausible bound, upper plausible bound)
OUTCOMES = {
    "grain_yield_g": {
        "n60": (66.0, 10.5),
        "n120": (77.5, 11.5),
        "vigour_loading": 6.0,
        "bounds": (35.0, 110.0),
        "decimals": 1,
    },
    "panicle_length_cm": {
        "n60": (25.2, 2.3),
        "n120": (26.9, 2.4),
        "vigour_loading": 1.1,
        "bounds": (18.0, 34.0),
        "decimals": 1,
    },
    "stem_brix_pct": {
        "n60": (13.3, 1.7),
        "n120": (12.9, 1.8),
        "vigour_loading": 0.35,
        "bounds": (8.0, 18.0),
        "decimals": 1,
    },
    "plant_height_cm": {
        "n60": (162.0, 13.5),
        "n120": (165.5, 14.0),
        "vigour_loading": 7.5,
        "bounds": (120.0, 210.0),
        "decimals": 1,
    },
}

GROUPS = ("n60", "n120")


def draw_group(rng: np.random.Generator, group: str, n: int) -> dict[str, np.ndarray]:
    """Draw all four outcomes for one nitrogen-rate group."""
    vigour = rng.normal(0.0, 1.0, size=n)
    columns: dict[str, np.ndarray] = {}
    for name, spec in OUTCOMES.items():
        mean, sd = spec[group]
        loading = spec["vigour_loading"]
        # Split the total spread between the shared vigour term and independent noise.
        noise_sd = float(np.sqrt(max(sd**2 - loading**2, 0.25)))
        values = mean + loading * vigour + rng.normal(0.0, noise_sd, size=n)
        low, high = spec["bounds"]
        values = np.clip(values, low, high)
        columns[name] = np.round(values, spec["decimals"])
    return columns


def main() -> None:
    rng = np.random.default_rng(SEED)

    rows = []
    plant_number = 1
    for group in GROUPS:
        columns = draw_group(rng, group, N_PER_GROUP)
        for i in range(N_PER_GROUP):
            rows.append(
                {
                    "plant_id": f"SB{plant_number:03d}",
                    "n_rate_group": group,
                    "grain_yield_g": f"{columns['grain_yield_g'][i]:.1f}",
                    "panicle_length_cm": f"{columns['panicle_length_cm'][i]:.1f}",
                    "stem_brix_pct": f"{columns['stem_brix_pct'][i]:.1f}",
                    "plant_height_cm": f"{columns['plant_height_cm'][i]:.1f}",
                }
            )
            plant_number += 1

    fieldnames = [
        "plant_id",
        "n_rate_group",
        "grain_yield_g",
        "panicle_length_cm",
        "stem_brix_pct",
        "plant_height_cm",
    ]
    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    assert len(rows) == 2 * N_PER_GROUP
    assert all(all(value != "" for value in row.values()) for row in rows)
    print(f"wrote {len(rows)} plant rows to {OUT_PATH.name}")


if __name__ == "__main__":
    main()
