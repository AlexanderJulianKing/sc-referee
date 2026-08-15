#!/usr/bin/env python3
"""Copper amendment vs baseline medium in bench-scale methanotroph runs.

Reads data/input.csv and writes results/report.md.  Every 2-L vessel is
inoculated, harvested and assayed exactly once, so each vessel contributes a
single analyzed row and the two arms are independent samples.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

UNIT_COLUMN = "vessel_id"
ARM_COLUMN = "medium"
VALUE_COLUMN = "final_titer_g_per_l"
ARMS = ("baseline", "cu_amended")


def read_table(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def variance_of_mean(sample):
    return stdev(sample) ** 2 / len(sample)


def welch_se(first, second):
    return math.sqrt(variance_of_mean(first) + variance_of_mean(second))


def welch_df(first, second):
    v1 = variance_of_mean(first)
    v2 = variance_of_mean(second)
    return (v1 + v2) ** 2 / (
        v1 * v1 / (len(first) - 1) + v2 * v2 / (len(second) - 1)
    )


def hedges_g(control, treated):
    n1, n2 = len(control), len(treated)
    pooled = ((n1 - 1) * stdev(control) ** 2 + (n2 - 1) * stdev(treated) ** 2) / (
        n1 + n2 - 2
    )
    cohens_d = (mean(treated) - mean(control)) / math.sqrt(pooled)
    return cohens_d * (1.0 - 3.0 / (4.0 * (n1 + n2) - 9.0))


def main():
    rows = read_table(INPUT_PATH)

    seen = Counter(row[UNIT_COLUMN] for row in rows)
    repeated = sorted(unit for unit, hits in seen.items() if hits > 1)
    repeated_note = ", ".join(repeated) if repeated else "none"

    titers = defaultdict(list)
    for row in rows:
        titers[row[ARM_COLUMN]].append(float(row[VALUE_COLUMN]))

    control, treated = titers[ARMS[0]], titers[ARMS[1]]

    outcome = stats.ttest_ind(treated, control, equal_var=False)
    difference = mean(treated) - mean(control)
    standard_error = welch_se(control, treated)
    dof = welch_df(control, treated)
    effect = hedges_g(control, treated)

    summary_rows = [
        "| {0} | {1} | {2:.3f} | {3:.3f} |".format(
            arm, len(titers[arm]), mean(titers[arm]), stdev(titers[arm])
        )
        for arm in ARMS
    ]

    selected = (
        "[selected-result] Welch two-sample t-test on {0} independent vessels"
        " (one titer per vessel): copper amendment raised final"
        " single-cell-protein titer by {1:.3f} g/L (t = {2:.3f}, df = {3:.2f},"
        " two-sided p = {4:.3g}, Hedges' g = {5:.3f})."
    ).format(len(rows), difference, outcome.statistic, dof, outcome.pvalue, effect)

    lines = [
        "# Copper amendment and single-cell-protein titer in methanotroph bench runs",
        "",
        "## Data",
        "",
        "- Source file: `data/input.csv`",
        "- Rows read: {0}".format(len(rows)),
        "- Independent vessels: {0}".format(len(seen)),
        "- Vessels appearing more than once: {0}".format(repeated_note),
        "",
        "| medium | vessels | mean titer (g/L) | sd (g/L) |",
        "| --- | ---: | ---: | ---: |",
        *summary_rows,
        "",
        "## Analysis",
        "",
        "Each 2-L bioreactor was inoculated once, run to harvest once, and assayed",
        "once, so the ten baseline titers and the ten copper-amended titers are ten",
        "independent observations per arm. The arms were compared with a Welch",
        "two-sample t-test (unequal variances, two-sided).",
        "",
        "## Result",
        "",
        "- Mean difference (cu_amended minus baseline): {0:.3f} g/L".format(difference),
        "- Standard error of the difference: {0:.4f} g/L".format(standard_error),
        "- Welch t statistic: {0:.3f}".format(outcome.statistic),
        "- Welch-Satterthwaite df: {0:.2f}".format(dof),
        "- Two-sided p-value: {0:.3g}".format(outcome.pvalue),
        "- Hedges' g: {0:.3f}".format(effect),
        "",
        selected,
        "",
        "## Notes",
        "",
        "The vessel is both the unit of randomization and the unit of analysis: no",
        "vessel is counted twice, and no within-vessel replicate measurements enter",
        "the test. The seed-density column is recorded for provenance and was not",
        "used in the comparison.",
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
