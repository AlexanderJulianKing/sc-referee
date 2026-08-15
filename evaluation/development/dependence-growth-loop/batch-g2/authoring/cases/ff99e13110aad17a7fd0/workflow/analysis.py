"""Cold-brew steeping trial: grind coarseness versus total dissolved solids.

Reads data/input.csv, compares the TDS readings of the two grind settings and
writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

DATA_FILE = Path("data") / "input.csv"
REPORT_FILE = Path("results") / "report.md"

SETTINGS = ("coarse", "fine")


def read_table(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def tds_for(table, setting):
    picked = [float(row["tds_percent"]) for row in table if row["grind"] == setting]
    return np.asarray(picked, dtype=float)


def welch_dof(left, right):
    a = left.var(ddof=1) / left.size
    b = right.var(ddof=1) / right.size
    return (a + b) ** 2 / (a * a / (left.size - 1) + b * b / (right.size - 1))


def p_phrase(pval):
    return "< 0.0001" if pval < 1e-4 else "= {:.4f}".format(pval)


def summary_line(setting, values):
    return "- {:<13} n = {:d}, mean TDS = {:.4f} %, SD = {:.4f} %".format(
        setting + " grind:", values.size, values.mean(), values.std(ddof=1)
    )


def main():
    table = read_table(DATA_FILE)
    samples = {setting: tds_for(table, setting) for setting in SETTINGS}
    coarse = samples["coarse"]
    fine = samples["fine"]

    tstat, pval = stats.ttest_ind(fine, coarse, equal_var=False)
    dof = welch_dof(fine, coarse)
    gap = float(fine.mean() - coarse.mean())
    stat_line = "t = {:.3f}, df = {:.1f}, p {}".format(
        float(tstat), dof, p_phrase(float(pval))
    )

    lines = [
        "# Cold-brew steeping: grind coarseness and total dissolved solids",
        "",
        "## Data",
        "",
        "{:d} total-dissolved-solids (TDS) readings taken from laboratory cold-brew".format(
            len(table)
        ),
        "steeping vessels. Each vessel was loaded with a single grind setting and",
        "sampled at draw times of 6, 12, 18 and 24 hours.",
        "",
        summary_line("coarse", coarse),
        summary_line("fine", fine),
        "",
        "## Analysis",
        "",
        "Welch two-sample t-test (two-sided, unequal variances) comparing the TDS",
        "readings recorded at the fine grind setting with those recorded at the",
        "coarse setting. Every row of the data file was supplied to the test as one",
        "observation.",
        "",
        "Mean difference (fine minus coarse): {:.4f} percentage points".format(gap),
        stat_line,
        "",
        "## Result",
        "",
        "[selected-result] Welch two-sample t-test on {:d} TDS readings ({:d} fine, {:d} coarse): mean difference fine minus coarse = {:.4f} percentage points, {}.".format(
            len(table), fine.size, coarse.size, gap, stat_line
        ),
        "",
        "## Interpretation",
        "",
        "Vessels filled with the fine grind returned higher total dissolved solids",
        "than vessels filled with the coarse grind across the sampled draw times.",
    ]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
