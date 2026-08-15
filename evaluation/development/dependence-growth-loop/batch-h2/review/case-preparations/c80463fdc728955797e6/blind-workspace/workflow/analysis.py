"""Cultivar comparison of leaf critical temperature (Tcrit).

Reads data/input.csv, compares the two cultivars, and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

GROUP_COLUMN = "cultivar"
TRAIT_COLUMN = "tcrit_c"
ORDER = ("Catuai", "Obata")


def read_leaf_table(path):
    """Collect Tcrit readings per cultivar, plus the shrub labels seen."""
    readings = {name: [] for name in ORDER}
    shrubs = {name: set() for name in ORDER}
    with path.open("r", encoding="ascii", newline="") as handle:
        for record in csv.DictReader(handle):
            cultivar = record[GROUP_COLUMN]
            readings[cultivar].append(float(record[TRAIT_COLUMN]))
            shrubs[cultivar].add(record["shrub_id"])
    return readings, shrubs


def welch_df(first, second):
    """Welch-Satterthwaite degrees of freedom for two independent samples."""
    term_a = first.var(ddof=1) / first.size
    term_b = second.var(ddof=1) / second.size
    denom = term_a ** 2 / (first.size - 1) + term_b ** 2 / (second.size - 1)
    return (term_a + term_b) ** 2 / denom


def main():
    readings, shrubs = read_leaf_table(INPUT_PATH)
    first = np.asarray(readings[ORDER[0]], dtype=float)
    second = np.asarray(readings[ORDER[1]], dtype=float)

    mean_a = float(first.mean())
    mean_b = float(second.mean())
    sd_a = float(first.std(ddof=1))
    sd_b = float(second.std(ddof=1))

    outcome = stats.ttest_ind(first, second, equal_var=False)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    dof = float(welch_df(first, second))

    total = int(first.size + second.size)
    gap = mean_a - mean_b
    p_text = "< 0.0001" if p_value < 1e-4 else "= {:.4f}".format(p_value)

    lines = [
        "# Leaf critical temperature in two coffee cultivars",
        "",
        "## Data",
        "",
        "Each row of `data/input.csv` is one leaf sampled for a chlorophyll-fluorescence",
        "temperature ramp; `tcrit_c` is the critical temperature (C) at which the rapid",
        f"rise in basal fluorescence begins. The file contains {total} leaf measurements",
        f"collected from field-grown shrubs of the cultivars {ORDER[0]} and {ORDER[1]}.",
        "",
        "## Analysis",
        "",
        "Every leaf measurement in the file was entered as a single observation, and the",
        "two cultivars were compared with Welch's two-sample t-test (unequal variances,",
        "two-sided) on `tcrit_c`.",
        "",
        "## Group summaries",
        "",
        "| cultivar | leaf measurements | shrubs sampled | mean tcrit_c (C) | SD (C) |",
        "| --- | --- | --- | --- | --- |",
        f"| {ORDER[0]} | {first.size} | {len(shrubs[ORDER[0]])} | {mean_a:.3f} | {sd_a:.3f} |",
        f"| {ORDER[1]} | {second.size} | {len(shrubs[ORDER[1]])} | {mean_b:.3f} | {sd_b:.3f} |",
        "",
        "## Result",
        "",
        f"[selected-result] Welch two-sample t-test on {total} leaf measurements: "
        f"t = {t_stat:.3f}, df = {dof:.2f}, two-sided p {p_text}; mean tcrit_c is "
        f"{gap:.3f} C higher in {ORDER[0]} ({mean_a:.3f} C, n = {first.size}) than in "
        f"{ORDER[1]} ({mean_b:.3f} C, n = {second.size}).",
        "",
        "The test statistic above spends one degree of freedom per leaf measurement, so",
        f"the reported df of {dof:.2f} comes from the {total} rows in the file.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
