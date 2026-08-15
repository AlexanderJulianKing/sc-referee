"""Do rock glaciers rooted in micaschist creep faster than those in orthogneiss?

Reads data/input.csv (one surveyed rock glacier per row) and writes
results/report.md. Every landform contributes exactly one velocity, so the rows
going into the two-sample test are mutually independent.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

DATA_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

UNIT_COL = "landform_id"
GROUP_COL = "bedrock_class"
VALUE_COL = "creep_velocity_cm_yr"


def read_rows(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def p_bracket(pvalue):
    for cutoff in (0.001, 0.01, 0.05):
        if pvalue < cutoff:
            return "p < %g" % cutoff
    return "p >= 0.05"


def main():
    rows = read_rows(DATA_PATH)

    ids = [row[UNIT_COL] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("landform_id must be unique: one row per landform")

    labels = sorted({row[GROUP_COL] for row in rows})
    if len(labels) != 2:
        raise ValueError("expected exactly two bedrock classes")
    first, second = labels

    def velocities(label):
        return np.array(
            [float(row[VALUE_COL]) for row in rows if row[GROUP_COL] == label],
            dtype=float,
        )

    x = velocities(first)
    y = velocities(second)

    n_x, n_y = x.size, y.size
    mean_x, mean_y = float(x.mean()), float(y.mean())
    var_x, var_y = float(x.var(ddof=1)), float(y.var(ddof=1))
    gap = mean_x - mean_y

    result = stats.ttest_ind(x, y, equal_var=False)

    term_x = var_x / n_x
    term_y = var_y / n_y
    welch_df = (term_x + term_y) ** 2 / (
        term_x ** 2 / (n_x - 1) + term_y ** 2 / (n_y - 1)
    )

    pooled_sd = (((n_x - 1) * var_x + (n_y - 1) * var_y) / (n_x + n_y - 2)) ** 0.5
    cohen_d = gap / pooled_sd
    verdict = p_bracket(float(result.pvalue))

    lines = []
    lines.append("# Bedrock lithology and downslope creep of alpine rock glaciers")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append(
        "Each row of `data/input.csv` is one rock glacier, surveyed once. No landform"
    )
    lines.append(
        "contributes more than one row, so the %d velocity values are %d independent"
        % (len(rows), len(rows))
    )
    lines.append("observations.")
    lines.append("")
    lines.append("## Groups")
    lines.append("")
    lines.append("| bedrock_class | n | mean creep (cm/yr) | SD (cm/yr) |")
    lines.append("| --- | --- | --- | --- |")
    lines.append(
        "| %s | %d | %.2f | %.2f |" % (first, n_x, mean_x, var_x ** 0.5)
    )
    lines.append(
        "| %s | %d | %.2f | %.2f |" % (second, n_y, mean_y, var_y ** 0.5)
    )
    lines.append("")
    lines.append("## Test")
    lines.append("")
    lines.append("Welch's two-sample t-test (unequal variances, two-sided) on")
    lines.append("%s by %s." % (VALUE_COL, GROUP_COL))
    lines.append("")
    lines.append(
        "Difference in means (%s - %s): %.2f cm/yr" % (first, second, gap)
    )
    lines.append(
        "t = %.2f, Welch-Satterthwaite df = %.1f, %s"
        % (result.statistic, welch_df, verdict)
    )
    lines.append("Cohen's d (pooled SD) = %.2f" % cohen_d)
    lines.append("")
    lines.append(
        "[selected-result] Welch two-sided t-test: %s-hosted rock glaciers creep"
        " %.2f cm/yr faster than %s-hosted ones (%.2f vs %.2f cm/yr; t = %.2f,"
        " df = %.1f, %s, Cohen's d = %.2f), one row per landform."
        % (first, gap, second, mean_x, mean_y, result.statistic, welch_df,
           verdict, cohen_d)
    )
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
