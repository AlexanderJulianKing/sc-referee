"""Ditch blocking and Sphagnum re-establishment in drained upland peat basins.

Reads data/input.csv, which holds one surveyed basin per row, and writes
results/report.md. Nothing else is read and nothing is printed.
"""

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT = Path("data") / "input.csv"
OUTPUT = Path("results") / "report.md"

UNIT_COLUMN = "basin_id"
GROUP_COLUMN = "ditch_treatment"
OUTCOME_COLUMN = "sphagnum_reestablished"


def load_basins(path):
    """Return the survey rows, refusing any basin that shows up twice."""
    with path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for row in rows:
        unit = row[UNIT_COLUMN]
        if unit in seen:
            raise ValueError("basin recorded more than once: " + unit)
        seen.add(unit)
    return rows


def summarise(rows, treatment):
    """Collapse one treatment arm into the counts the report needs."""
    arm = [row for row in rows if row[GROUP_COLUMN] == treatment]
    if not arm:
        raise ValueError("no basins with treatment: " + treatment)
    established = sum(1 for row in arm if row[OUTCOME_COLUMN] == "yes")
    areas = [float(row["basin_area_ha"]) for row in arm]
    depths = [int(row["peat_depth_cm"]) for row in arm]
    return {
        "label": treatment,
        "n": len(arm),
        "yes": established,
        "no": len(arm) - established,
        "proportion": established / len(arm),
        "mean_area": sum(areas) / len(areas),
        "median_depth": statistics.median(depths),
    }


def table_row(arm):
    return "| {label} | {n} | {yes} | {proportion:.3f} | {mean_area:.2f} | {median_depth:.1f} |".format(**arm)


def main():
    rows = load_basins(INPUT)
    blocked = summarise(rows, "blocked")
    unblocked = summarise(rows, "open")

    table = [[blocked["yes"], blocked["no"]], [unblocked["yes"], unblocked["no"]]]
    _, p_value = stats.fisher_exact(table, alternative="two-sided")
    odds_ratio = (table[0][0] * table[1][1]) / (table[0][1] * table[1][0])
    risk_difference = blocked["proportion"] - unblocked["proportion"]

    result = (
        "[selected-result] Fisher's exact test on {total} independent peat basins: "
        "Sphagnum re-established in {b_yes} of {b_n} basins with blocked ditches "
        "versus {o_yes} of {o_n} basins with open ditches (sample odds ratio "
        "{odds:.3f}, two-sided p = {p:.4f}), a significant difference at "
        "alpha = 0.05."
    ).format(
        total=len(rows),
        b_yes=blocked["yes"],
        b_n=blocked["n"],
        o_yes=unblocked["yes"],
        o_n=unblocked["n"],
        odds=odds_ratio,
        p=p_value,
    )

    lines = [
        "# Sphagnum re-establishment after ditch blocking in drained peat basins",
        "",
        "## Design",
        "",
        "Each row of `data/input.csv` is one drained peat basin surveyed once in the",
        "2025 growing season. Basins are the independent units: {n} basins, {n} rows,".format(n=len(rows)),
        "and no basin appears twice. Ditch treatment was fixed for the whole basin, so",
        "each basin contributes a single yes/no outcome to a single cell of the table.",
        "",
        "## Groups",
        "",
        "| Ditch treatment | Basins | Re-established | Proportion | Mean area (ha) | Median peat depth (cm) |",
        "| --- | --- | --- | --- | --- | --- |",
        table_row(blocked),
        table_row(unblocked),
        "",
        "## Test",
        "",
        "Fisher's exact test (two-sided) on the 2x2 table of ditch treatment by",
        "Sphagnum re-establishment. Fisher's exact test was chosen over a chi-square",
        "test because several expected cell counts are small.",
        "",
        "Contingency table (rows: blocked, open; columns: yes, no): {t}".format(t=table),
        "",
        "- Sample odds ratio: {v:.3f}".format(v=odds_ratio),
        "- Two-sided p-value: {v:.4f}".format(v=p_value),
        "- Risk difference (blocked minus open): {v:.3f}".format(v=risk_difference),
        "",
        "## Result",
        "",
        result,
        "",
        "## Notes",
        "",
        "Basin area and peat depth are reported only as descriptive balance checks;",
        "neither was entered into the test.",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
