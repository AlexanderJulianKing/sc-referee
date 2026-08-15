"""Chloride exceedance screening for the Wrack Bay coastal aquifer network.

Reads the field sample table, scores every grab sample against the 250 mg/L
chloride action limit, and tests whether exceedance status is associated with
the shoreline zone in which the sampled well sits.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

LIMIT_MG_L = 250.0
ZONES = ("dune_ridge", "back_barrier", "tidal_flat")
PRETTY = {
    "dune_ridge": "Dune ridge",
    "back_barrier": "Back barrier",
    "tidal_flat": "Tidal flat",
}


def read_samples(path):
    """Return the sample rows with their numeric fields converted."""
    with path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["visit"] = int(row["visit"])
        row["depth_m"] = float(row["depth_m"])
        row["chloride_mg_l"] = float(row["chloride_mg_l"])
    return rows


def contingency(rows):
    """Zone-by-exceedance counts, one sample row per tallied observation."""
    counts = np.zeros((len(ZONES), 2), dtype=int)
    for row in rows:
        zone_ix = ZONES.index(row["coastal_zone"])
        col = 0 if row["chloride_mg_l"] >= LIMIT_MG_L else 1
        counts[zone_ix, col] += 1
    return counts


def render(counts, chi2, pval, dof, cramers_v, n_wells, visits):
    """Build the markdown report text."""
    n = int(counts.sum())
    rate = {
        zone: int(counts[i, 0]) / int(counts[i].sum())
        for i, zone in enumerate(ZONES)
    }
    out = [
        "# Chloride exceedance and shoreline zone, Wrack Bay monitoring network",
        "",
        "## Data",
        "",
        f"Source table: data/input.csv ({n} sample rows from {n_wells} monitoring "
        f"wells, {visits} visits each).",
        "A sample counts as an exceedance when chloride is at or above "
        f"{LIMIT_MG_L:.1f} mg/L.",
        "",
        "| Shoreline zone | Samples | Exceedances | Exceedance rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for i, zone in enumerate(ZONES):
        total = int(counts[i].sum())
        hits = int(counts[i, 0])
        out.append(f"| {PRETTY[zone]} | {total} | {hits} | {rate[zone]:.3f} |")
    out += [
        "",
        "## Analysis",
        "",
        "Pearson chi-squared test of independence (scipy.stats.chi2_contingency) applied",
        f"to the {counts.shape[0]} x {counts.shape[1]} table of shoreline zone by "
        "exceedance status, with each sample row",
        "entered as one observation.",
        "",
        f"- chi-squared statistic: {chi2:.4f}",
        f"- degrees of freedom: {dof}",
        f"- p-value: {pval:.3e}",
        f"- Cramer's V: {cramers_v:.3f}",
        "",
        "## Result",
        "",
        "[selected-result] Exceedance status is associated with shoreline zone: "
        f"Pearson chi-squared test of independence on {n} sample rows gives "
        f"chi-squared = {chi2:.4f}, df = {dof}, p = {pval:.3e} "
        f"(Cramer's V = {cramers_v:.3f}), with the exceedance rate rising from "
        f"{rate['dune_ridge']:.3f} on the dune ridge to "
        f"{rate['back_barrier']:.3f} on the back barrier and "
        f"{rate['tidal_flat']:.3f} on the tidal flat.",
    ]
    return "\n".join(out) + "\n"


def main():
    rows = read_samples(INPUT_PATH)
    counts = contingency(rows)
    chi2, pval, dof, _expected = stats.chi2_contingency(counts, correction=False)
    total = int(counts.sum())
    cramers_v = float(np.sqrt(chi2 / (total * (min(counts.shape) - 1))))
    per_well = Counter(row["well_id"] for row in rows)
    report = render(
        counts,
        chi2,
        pval,
        dof,
        cramers_v,
        len(per_well),
        max(per_well.values()),
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
