"""Deterministic generator for the camel dairy mineral supplement dataset.

Running this script rewrites the two CSV analysis inputs:

  camel_milk_outcomes.csv        subject-level table, one row per dam
  pipeline_family_results.csv    upstream stage results, one row per declared outcome

Both files are a pure function of SEED, so re-running reproduces them byte for byte.

The pipeline results file stands in for a table handed over by the dairy unit's
upstream statistics stage. Those raw and multiplicity-adjusted p-values are
therefore computed here, at data-creation time, so that the file exists as an
input on disk.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

SEED = 20260824
N_PER_GROUP = 48
GROUPS = ("mineral_standard", "mineral_enriched")

OUT_DIR = Path(__file__).resolve().parent
RAW_CSV = OUT_DIR / "camel_milk_outcomes.csv"
PIPELINE_CSV = OUT_DIR / "pipeline_family_results.csv"

# Declared outcome family, in the protocol order.
# name -> (standard mean, enriched mean, within-group sd, plausible low, plausible high, decimals)
OUTCOMES = {
    "milk_yield_l_per_day": (7.10, 8.05, 1.45, 3.0, 12.0, 2),
    "milk_fat_pct": (3.32, 3.40, 0.40, 2.0, 4.5, 2),
    "milk_protein_pct": (3.08, 3.12, 0.26, 2.5, 4.0, 2),
    "body_condition_score": (3.05, 3.32, 0.44, 2.0, 4.5, 1),
    "plasma_glucose_mmol_l": (5.32, 5.41, 0.68, 3.5, 7.5, 2),
}


def make_subject_table(rng: np.random.Generator) -> list[dict[str, object]]:
    """One row per dam: identifier, regimen, and all five declared outcomes."""
    n_total = 2 * N_PER_GROUP
    group_labels = [GROUPS[0]] * N_PER_GROUP + [GROUPS[1]] * N_PER_GROUP

    # A per-dam random effect gives the outcomes mild, realistic co-variation:
    # a dam in better shape tends to milk a little more.
    dam_effect = rng.normal(0.0, 1.0, size=n_total)

    columns: dict[str, np.ndarray] = {}
    for name, (mu_std, mu_enr, sd, low, high, decimals) in OUTCOMES.items():
        means = np.array(
            [mu_std if g == GROUPS[0] else mu_enr for g in group_labels], dtype=float
        )
        shared = 0.35 if name in ("milk_yield_l_per_day", "body_condition_score") else 0.10
        noise = shared * dam_effect + np.sqrt(max(1.0 - shared**2, 0.0)) * rng.normal(
            0.0, 1.0, size=n_total
        )
        values = means + sd * noise
        values = np.clip(values, low, high)
        columns[name] = np.round(values, decimals)

    rows: list[dict[str, object]] = []
    for i in range(n_total):
        row: dict[str, object] = {
            "camel_id": f"CAM{i + 1:03d}",
            "supplement_group": group_labels[i],
        }
        for name, (_, _, _, _, _, decimals) in OUTCOMES.items():
            row[name] = f"{columns[name][i]:.{decimals}f}"
        rows.append(row)
    return rows


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjustment across the whole declared family."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * p_values[idx])
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted


def make_pipeline_table(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Emulate the upstream stage: five two-group tests, then one family-wide adjustment."""
    raw_p: list[float] = []
    for name in OUTCOMES:
        std = np.array(
            [float(r[name]) for r in rows if r["supplement_group"] == GROUPS[0]]
        )
        enr = np.array(
            [float(r[name]) for r in rows if r["supplement_group"] == GROUPS[1]]
        )
        raw_p.append(float(stats.ttest_ind(enr, std, equal_var=False).pvalue))

    adjusted_p = holm_adjust(raw_p)
    return [
        {
            "outcome_name": name,
            "raw_p_value": f"{raw:.6f}",
            "adjusted_p_value": f"{adj:.6f}",
        }
        for name, raw, adj in zip(OUTCOMES, raw_p, adjusted_p)
    ]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    subject_rows = make_subject_table(rng)
    pipeline_rows = make_pipeline_table(subject_rows)

    write_csv(RAW_CSV, subject_rows)
    write_csv(PIPELINE_CSV, pipeline_rows)

    print(f"wrote {RAW_CSV.name}: {len(subject_rows)} rows")
    print(f"wrote {PIPELINE_CSV.name}: {len(pipeline_rows)} rows")
    for row in pipeline_rows:
        print(f"  {row['outcome_name']}: raw={row['raw_p_value']} adj={row['adjusted_p_value']}")


if __name__ == "__main__":
    main()
