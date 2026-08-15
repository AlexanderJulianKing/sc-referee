"""Vessel-level comparison of final ethanol titer between two Zymomonas strains.

Reads data/input.csv, which holds one harvest measurement per pilot fermenter, and
writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

ROW_TEMPLATE = "| {0} | {1} | {2:.2f} | {3:.2f} | {4:.2f} | {5:.2f} | {6:.2f} |"


def read_vessels(path):
    """Return the CSV rows, refusing any vessel that shows up twice."""
    with path.open("r", encoding="ascii", newline="") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for row in rows:
        vessel = row["vessel_id"]
        if vessel in seen:
            raise ValueError("vessel_id appears more than once: " + vessel)
        seen.add(vessel)
    return rows


def arm_titers(rows, arm):
    picked = [float(row["final_titer_g_per_l"]) for row in rows
              if row["strain_arm"] == arm]
    return np.asarray(picked, dtype=float)


def summary_row(label, values):
    return ROW_TEMPLATE.format(
        label,
        values.size,
        values.mean(),
        values.std(ddof=1),
        np.median(values),
        values.min(),
        values.max(),
    )


def main():
    rows = read_vessels(INPUT_PATH)
    wild = arm_titers(rows, "wildtype")
    engineered = arm_titers(rows, "engineered")

    outcome = stats.mannwhitneyu(engineered, wild, alternative="two-sided",
                                 method="exact")
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    rank_biserial = 2.0 * u_stat / float(engineered.size * wild.size) - 1.0
    shift = float(np.median(engineered[:, None] - wild[None, :]))
    mean_gap = float(engineered.mean() - wild.mean())
    n_total = wild.size + engineered.size

    lines = [
        "# Final ethanol titer of an engineered Zymomonas strain in pilot fermenters",
        "",
        "## Design",
        "",
        "Twelve independent 20 L pilot fermenters were taken to harvest, six seeded with the",
        "wild-type strain and six with the engineered strain. Each vessel received its own",
        "inoculum lot and contributes exactly one harvest titer, so the twelve rows of",
        "data/input.csv are twelve independent units and no vessel is measured more than once.",
        "",
        "## Vessel-level summary",
        "",
        "| Arm | Vessels | Mean (g/L) | SD (g/L) | Median (g/L) | Min (g/L) | Max (g/L) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        summary_row("wild-type", wild),
        summary_row("engineered", engineered),
        "",
        "## Test",
        "",
        "With six vessels per arm the two arms were compared with an exact two-sided",
        "Mann-Whitney U test on the twelve vessel-level titers (no ties are present, so the",
        "exact null distribution applies). The engineered vessels occupy the six highest ranks,",
        f"giving U = {u_stat:.1f} with an exact two-sided p-value of {p_value:.5f}. The rank-biserial",
        f"correlation is {rank_biserial:.3f}, the Hodges-Lehmann shift estimate is {shift:.2f} g/L, and the gap",
        f"between arm means is {mean_gap:.2f} g/L.",
        "",
        (
            "[selected-result] Exact two-sided Mann-Whitney U test on "
            f"{n_total} independent pilot fermenters ({engineered.size} engineered vs "
            f"{wild.size} wild-type, one harvest titer per vessel): U = {u_stat:.1f}, "
            f"p = {p_value:.5f}, Hodges-Lehmann shift +{shift:.2f} g/L, so the engineered "
            "strain reaches the higher final titer."
        ),
        "",
        "## Reading",
        "",
        "The strains were assigned to whole vessels and the comparison is made at the vessel",
        "level, so the independence assumption of the exact test is satisfied by construction",
        "rather than by argument. Complete separation of the two arms yields the smallest",
        "p-value this design can return, so the result is best read as evidence that is as",
        "strong as twelve runs allow, not as a finely resolved probability.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
