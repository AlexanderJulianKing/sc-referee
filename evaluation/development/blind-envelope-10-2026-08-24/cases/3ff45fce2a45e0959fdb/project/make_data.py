"""Deterministic generator for the community wound-care dressing comparison dataset.

Writes `venous_ulcer_dressings.csv`: one row per patient, one column per declared
outcome, plus a patient identifier and the dressing-group label.

Ninety adult patients with a single chronic venous leg ulcer, forty-five on a
standard foam dressing and forty-five on an alginate dressing, all under the same
compression bandaging regimen, each followed for twelve weeks.

Every outcome is drawn from a per-patient baseline-severity latent so that the six
outcomes move together the way they do in a real wound clinic (a bigger, wetter,
more painful ulcer heals more slowly and scores worse on quality of life). Group
means differ modestly on some outcomes and are essentially the same on others.

Run with the repository virtual environment:
    .venv/bin/python make_data.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260824
N_PER_GROUP = 45
GROUPS = ("dressing_foam", "dressing_alginate")

OUT_PATH = Path(__file__).resolve().parent / "venous_ulcer_dressings.csv"

COLUMNS = [
    "patient_id",
    "dressing_group",
    "area_reduction_pct",
    "pain_vas_mm",
    "exudate_score",
    "periwound_erythema_mm",
    "days_to_half_healing",
    "wound_qol_score",
]

# Per-group location and spread for each outcome, before the severity latent and
# before clipping to the plausible clinical range.
#   key: (foam_mean, alginate_mean, residual_sd, severity_loading, low, high)
OUTCOME_SPEC = {
    "area_reduction_pct": (57.0, 67.0, 15.0, -9.0, 0.0, 95.0),
    "pain_vas_mm": (44.0, 41.5, 11.0, 7.0, 15.0, 75.0),
    "exudate_score": (4.7, 3.7, 1.2, 0.9, 1.0, 8.0),
    "periwound_erythema_mm": (9.6, 9.0, 4.0, 2.6, 0.0, 25.0),
    "days_to_half_healing": (46.0, 39.0, 13.0, 8.5, 10.0, 84.0),
    "wound_qol_score": (66.5, 69.0, 9.5, -5.5, 40.0, 90.0),
}


def draw_outcome(rng, spec, severity, group_index):
    """Draw one outcome column for one group."""
    foam_mean, alginate_mean, resid_sd, loading, low, high = spec
    mean = foam_mean if group_index == 0 else alginate_mean
    values = mean + loading * severity + rng.normal(0.0, resid_sd, size=severity.size)
    return np.clip(values, low, high)


def build_group(rng, group_index, id_start):
    """Build the rows for one dressing group."""
    # Baseline ulcer severity, standardised; the two arms are balanced by design.
    severity = rng.normal(0.0, 1.0, size=N_PER_GROUP)
    severity = (severity - severity.mean()) / severity.std(ddof=0)

    drawn = {
        name: draw_outcome(rng, spec, severity, group_index)
        for name, spec in OUTCOME_SPEC.items()
    }

    rows = []
    for i in range(N_PER_GROUP):
        rows.append(
            {
                "patient_id": f"WLU-{id_start + i:03d}",
                "dressing_group": GROUPS[group_index],
                "area_reduction_pct": round(float(drawn["area_reduction_pct"][i]), 1),
                "pain_vas_mm": int(round(float(drawn["pain_vas_mm"][i]))),
                "exudate_score": round(float(drawn["exudate_score"][i]), 1),
                "periwound_erythema_mm": round(
                    float(drawn["periwound_erythema_mm"][i]), 1
                ),
                "days_to_half_healing": int(round(float(drawn["days_to_half_healing"][i]))),
                "wound_qol_score": int(round(float(drawn["wound_qol_score"][i]))),
            }
        )
    return rows


def main():
    rng = np.random.default_rng(SEED)

    rows = build_group(rng, 0, id_start=1)
    rows += build_group(rng, 1, id_start=1 + N_PER_GROUP)

    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_PATH.name}")


if __name__ == "__main__":
    main()
