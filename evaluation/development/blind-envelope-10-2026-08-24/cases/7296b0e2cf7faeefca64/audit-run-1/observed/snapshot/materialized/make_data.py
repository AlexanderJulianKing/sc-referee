"""Generate the calf feeding-trial data file for the winter pellet comparison.

Deterministic: a fixed seed drives a single numpy Generator, so re-running this
script reproduces calves.csv byte for byte.

Design encoded here
-------------------
78 first-winter reindeer calves in the corral feeding period, 39 fed the
established pellet and 39 fed the new protein / lichen-substitute blend.
Each calf is measured once at the end of the ten-week period on three
outcomes: average daily body weight gain, serum urea, and haematocrit.

A per-calf latent "condition" term (entry body condition, appetite, dam
quality) is shared across the outcomes so that gain, urea and haematocrit are
mildly correlated within a calf, as they are in real animals.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260824
N_PER_GROUP = 39
GROUPS = ("pellet_established", "pellet_new")

# Group-level generating parameters, on the natural measurement scale.
PARAMS = {
    "pellet_established": {
        "gain_mean": 268.0,
        "gain_sd": 50.0,
        "urea_mean": 4.35,
        "urea_sd": 0.82,
        "hct_mean": 38.6,
        "hct_sd": 2.95,
    },
    "pellet_new": {
        "gain_mean": 289.0,
        "gain_sd": 53.0,
        "urea_mean": 4.95,
        "urea_sd": 0.88,
        "hct_mean": 38.9,
        "hct_sd": 2.90,
    },
}

# How strongly the shared per-calf condition term loads on each outcome,
# expressed as a fraction of that outcome's group standard deviation.
CONDITION_LOADING = {"gain": 0.45, "urea": 0.20, "hct": 0.30}

# Plausible physiological bounds for a first-winter calf; values are clipped
# so no impossible number reaches the file.
BOUNDS = {
    "gain": (100.0, 450.0),
    "urea": (2.0, 7.5),
    "hct": (30.0, 48.0),
}


def build_frame(rng: np.random.Generator) -> pd.DataFrame:
    n_total = N_PER_GROUP * len(GROUPS)

    calf_ids = [f"RC-{i:03d}" for i in range(1, n_total + 1)]

    # Balanced allocation: 39 per group, order shuffled across the ear-tag
    # sequence so group is not confounded with identifier order.
    labels = np.array([GROUPS[0]] * N_PER_GROUP + [GROUPS[1]] * N_PER_GROUP)
    rng.shuffle(labels)

    condition = rng.normal(0.0, 1.0, size=n_total)

    gain = np.empty(n_total)
    urea = np.empty(n_total)
    hct = np.empty(n_total)

    for group in GROUPS:
        mask = labels == group
        k = int(mask.sum())
        p = PARAMS[group]

        for key, target, mean, sd in (
            ("gain", gain, p["gain_mean"], p["gain_sd"]),
            ("urea", urea, p["urea_mean"], p["urea_sd"]),
            ("hct", hct, p["hct_mean"], p["hct_sd"]),
        ):
            load = CONDITION_LOADING[key]
            # Split the group SD between the shared condition term and
            # independent measurement / biological noise so the marginal SD
            # stays at the intended value.
            shared = load * sd * condition[mask]
            independent = rng.normal(0.0, sd * np.sqrt(1.0 - load**2), size=k)
            target[mask] = mean + shared + independent

    gain = np.clip(gain, *BOUNDS["gain"])
    urea = np.clip(urea, *BOUNDS["urea"])
    hct = np.clip(hct, *BOUNDS["hct"])

    return pd.DataFrame(
        {
            "calf_id": calf_ids,
            "feed_group": labels,
            "daily_gain_g_per_day": np.round(gain, 1),
            "serum_urea_mmol_l": np.round(urea, 2),
            "haematocrit_pct": np.round(hct, 1),
        }
    )


def main() -> None:
    rng = np.random.default_rng(SEED)
    frame = build_frame(rng)

    assert len(frame) == N_PER_GROUP * len(GROUPS)
    assert frame["calf_id"].is_unique
    assert not frame.isna().to_numpy().any()
    assert sorted(frame["feed_group"].unique()) == sorted(GROUPS)
    assert (frame["feed_group"].value_counts() == N_PER_GROUP).all()

    out_path = Path(__file__).resolve().parent / "calves.csv"
    frame.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
