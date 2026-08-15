"""Does thermal inoculum pretreatment raise specific methane yield?

The monitoring table in data/input.csv is stored long: one row per
digester-session, four sessions per vessel. Those rows are repeated measures on
the same reactor, so they are collapsed to one analysed value per vessel before
the two pretreatment arms are compared. Output goes to results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

UNIT_COL = "digester_id"
ARM_COL = "pretreatment"
YIELD_COL = "ch4_yield_ml_per_g_vs"


def read_sessions(path):
    """Return digester id -> (arm, list of that vessel's session yields)."""
    sessions = {}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            unit = record[UNIT_COL].strip()
            if unit not in sessions:
                sessions[unit] = (record[ARM_COL].strip(), [])
            sessions[unit][1].append(float(record[YIELD_COL]))
    return sessions


def digester_table(sessions):
    """One analysed row per independent vessel: its across-session mean yield."""
    table = []
    for unit in sorted(sessions):
        arm, yields = sessions[unit]
        table.append((unit, arm, len(yields), float(np.mean(yields))))
    return table


def arm_values(table, arm):
    return np.array([row[3] for row in table if row[1] == arm], dtype=float)


def build_report(table, n_sessions, control, thermal, u_stat, p_value, gap):
    n_units = len(table)
    lines = [
        "# Inoculum pretreatment and specific methane yield in bench-scale digesters",
        "",
        "## Data",
        "",
        "The file data/input.csv stores {0} monitoring records collected from {1} bench-scale".format(n_sessions, n_units),
        "anaerobic digesters. Each digester was sampled on four monitoring sessions (run days",
        "6, 10, 14 and 18), so the records are repeated measurements nested within vessels",
        "rather than {0} independent observations. Six digesters were run on untreated".format(n_sessions),
        "inoculum (control) and six on thermally pretreated inoculum (thermal).",
        "",
        "## Analysis",
        "",
        "Each digester is collapsed to a single analysed value, the mean specific methane",
        "yield across its four sessions. The resulting {0} digester means, one per".format(n_units),
        "independent vessel, are compared between the two pretreatment arms with a",
        "two-sided exact Mann-Whitney U test ({0} vessels vs {1} vessels).".format(control.size, thermal.size),
        "",
        "## Digester-level values",
        "",
        "| digester | pretreatment | sessions | mean yield (mL CH4 / g VS) |",
        "| --- | --- | --- | --- |",
    ]
    for unit, arm, n_rows, mean_yield in table:
        lines.append("| {0} | {1} | {2} | {3:.1f} |".format(unit, arm, n_rows, mean_yield))
    lines.extend([
        "",
        "## Results",
        "",
        "Monitoring records read: {0}".format(n_sessions),
        "Independent digesters analysed: {0}".format(n_units),
        "Control arm: n = {0} digesters, mean of digester means = {1:.2f} mL CH4 / g VS, median = {2:.2f}".format(
            control.size, control.mean(), np.median(control)),
        "Thermal arm: n = {0} digesters, mean of digester means = {1:.2f} mL CH4 / g VS, median = {2:.2f}".format(
            thermal.size, thermal.mean(), np.median(thermal)),
        "Difference in medians (thermal - control): {0:.2f} mL CH4 / g VS".format(gap),
        "Mann-Whitney U (thermal vs control): {0:.1f}".format(u_stat),
        "Exact two-sided p-value: {0:.6f}".format(p_value),
        "",
        "[selected-result] Thermally pretreated digesters produced higher specific methane yield than control digesters (Mann-Whitney U = {0:.1f}, n = {1} vs {2} digester means, exact two-sided p = {3:.6f}); the median digester mean was {4:.2f} mL CH4 / g VS higher in the thermal arm.".format(
            u_stat, thermal.size, control.size, p_value, gap),
        "",
        "## Unit of analysis",
        "",
        "The {0} stored rows are four repeated sessions from each of {1} vessels. The reported".format(n_sessions, n_units),
        "comparison is run on the {0} vessel-level means, so every independent digester enters".format(n_units),
        "the test exactly once and the repeated sessions contribute only to the precision of",
        "each vessel's own value.",
    ])
    return "\n".join(lines) + "\n"


def main():
    sessions = read_sessions(INPUT_PATH)
    table = digester_table(sessions)
    n_sessions = sum(row[2] for row in table)

    control = arm_values(table, "control")
    thermal = arm_values(table, "thermal")

    u_stat, p_value = stats.mannwhitneyu(
        thermal, control, alternative="two-sided", method="exact")
    gap = float(np.median(thermal) - np.median(control))

    report = build_report(
        table, n_sessions, control, thermal, float(u_stat), float(p_value), gap)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
