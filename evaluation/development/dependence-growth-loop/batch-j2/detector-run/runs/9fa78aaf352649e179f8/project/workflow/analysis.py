"""Tank-level comparison of routine oxygen uptake in juvenile Atlantic salmon.

Reads data/input.csv (one row per overnight respirometry session) and writes
results/report.md. The overnight sessions are repeated measurements on the same
tanks, so they are averaged within a tank before any test is run.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

CONTROL = "control"
SUPPLEMENT = "bglucan"
DIET_LABEL = {CONTROL: "control", SUPPLEMENT: "beta-glucan"}


def read_sessions(path):
    """Return one (tank_id, diet, mo2) tuple per session row."""
    sessions = []
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            sessions.append(
                (
                    record["tank_id"],
                    record["diet"],
                    float(record["mo2_mg_kg_h"]),
                )
            )
    return sessions


def collapse_to_tanks(sessions):
    """Average the repeated sessions of a tank into a single tank-level value."""
    diet_of = {}
    readings = {}
    for tank_id, diet, mo2 in sessions:
        diet_of[tank_id] = diet
        readings.setdefault(tank_id, []).append(mo2)
    tanks = []
    for tank_id in sorted(readings):
        values = readings[tank_id]
        tanks.append(
            {
                "tank_id": tank_id,
                "diet": diet_of[tank_id],
                "sessions": len(values),
                "mean_mo2": float(np.mean(values)),
            }
        )
    return tanks


def group_means(tanks, diet):
    """One value per tank for the requested diet."""
    return np.array(
        [tank["mean_mo2"] for tank in tanks if tank["diet"] == diet], dtype=float
    )


def build_report(tanks, n_sessions):
    control = group_means(tanks, CONTROL)
    supplemented = group_means(tanks, SUPPLEMENT)
    n_tanks = len(tanks)
    n_control = control.size
    n_supp = supplemented.size

    test = stats.mannwhitneyu(
        supplemented, control, alternative="two-sided", method="exact"
    )
    u_stat = float(test.statistic)
    p_value = float(test.pvalue)
    rank_biserial = 2.0 * u_stat / float(n_control * n_supp) - 1.0

    ctrl_mean = float(np.mean(control))
    supp_mean = float(np.mean(supplemented))
    ctrl_median = float(np.median(control))
    supp_median = float(np.median(supplemented))
    median_gap = supp_median - ctrl_median

    lines = [
        "# Routine metabolic rate of juvenile Atlantic salmon on a beta-glucan diet",
        "",
        "## Design and data",
        "",
        f"The file data/input.csv contains {n_sessions} overnight respirometry sessions recorded on",
        f"{n_tanks} recirculating tanks: {n_control} fed the control ration and {n_supp} fed the same ration with a",
        "beta-glucan supplement. Each tank was measured on three or four separate nights, so the",
        f"{n_sessions} rows are repeated sessions rather than {n_sessions} independent observations. Diet was",
        "randomised to whole tanks, and each tank ran on its own water loop, feeder and biofilter,",
        "so the tank is the independent experimental unit.",
        "",
        "## Analysis",
        "",
        "Sessions were averaged within each tank before any test was run, so every tank",
        "contributes exactly one value (mass-specific oxygen uptake, MO2, in mg O2 kg^-1 h^-1) to",
        "the comparison. The two diets were then compared with a two-sided exact Mann-Whitney U",
        f"test on the {n_tanks} tank means ({n_control} control vs {n_supp} beta-glucan). The individual session rows were",
        "never entered into the test.",
        "",
        "## Tank-level summary",
        "",
        "| tank | diet | sessions | mean MO2 (mg O2 kg^-1 h^-1) |",
        "| --- | --- | --- | --- |",
    ]

    for tank in tanks:
        lines.append(
            "| {0} | {1} | {2} | {3:.2f} |".format(
                tank["tank_id"],
                DIET_LABEL[tank["diet"]],
                tank["sessions"],
                tank["mean_mo2"],
            )
        )

    lines.extend(
        [
            "",
            "## Result",
            "",
            f"Averaged over tanks, MO2 was {supp_mean:.2f} mg O2 kg^-1 h^-1 on the beta-glucan diet and {ctrl_mean:.2f}",
            f"on the control diet; the tank medians were {supp_median:.1f} and {ctrl_median:.1f}, a median difference of {median_gap:.1f}",
            f"mg O2 kg^-1 h^-1. The exact Mann-Whitney U test on the {n_tanks} tank means gives U = {u_stat:.1f},",
            f"p = {p_value:.6f}, rank-biserial correlation {rank_biserial:.3f}.",
            "",
            f"[selected-result] Tanks fed the beta-glucan supplement had higher routine oxygen uptake than control tanks (two-sided exact Mann-Whitney U on {n_supp} vs {n_control} tank means, U = {u_stat:.1f}, p = {p_value:.6f}, rank-biserial {rank_biserial:.3f}).",
            "",
            "## Notes",
            "",
            "Tanks T05 and T10 each lost one night to a chiller fault; the unbalanced session counts",
            "change the precision of those two tank means but not the number of independent units,",
            "which stays at one per tank. A rank test was preferred to a t test because six tanks per",
            "diet give little leverage for judging normality.",
        ]
    )
    return lines


def main():
    sessions = read_sessions(INPUT_PATH)
    tanks = collapse_to_tanks(sessions)
    lines = build_report(tanks, len(sessions))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
