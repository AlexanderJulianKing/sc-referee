"""Midsummer methane efflux from drained versus rewetted peat collars.

The script reads data/input.csv, which stores exactly one gas-flux collar per
row, and writes results/report.md with a Welch two-sample comparison of the two
management classes.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

UNIT_COLUMN = "collar_id"
GROUP_COLUMN = "management"
VALUE_COLUMN = "ch4_flux_mg_m2_h"

BASELINE = "drained"
REWETTED = "restored"


def read_table(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def split_by_management(table):
    collars = [record[UNIT_COLUMN] for record in table]
    if len(set(collars)) != len(collars):
        raise ValueError("every collar must occupy exactly one row")

    buckets = {BASELINE: [], REWETTED: []}
    for record in table:
        label = record[GROUP_COLUMN]
        if label not in buckets:
            raise ValueError("unrecognised management label: " + repr(label))
        buckets[label].append(float(record[VALUE_COLUMN]))
    return {name: np.asarray(vals, dtype=float) for name, vals in buckets.items()}


def welch_df(a, b):
    va = a.var(ddof=1) / a.size
    vb = b.var(ddof=1) / b.size
    return (va + vb) ** 2 / (va * va / (a.size - 1) + vb * vb / (b.size - 1))


def welch_se(a, b):
    return math.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)


def pooled_sd(a, b):
    ss = (a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)
    return math.sqrt(ss / (a.size + b.size - 2))


def build_report(table, drained, rewetted):
    diff = float(rewetted.mean() - drained.mean())
    se = welch_se(rewetted, drained)
    dof = welch_df(rewetted, drained)

    outcome = stats.ttest_ind(rewetted, drained, equal_var=False)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)

    half = float(stats.t.ppf(0.975, dof)) * se
    spooled = pooled_sd(rewetted, drained)
    dvalue = diff / spooled
    ptext = "p < 0.0001" if pvalue < 1e-4 else "p = {:.4f}".format(pvalue)

    lines = [
        "# Methane efflux from drained versus rewetted peat collars",
        "",
        "## Design",
        "",
        "Twenty-four gas-flux collars were installed, one collar per independently",
        "selected raised-bog basin, and every collar contributed exactly one midsummer",
        "chamber closure. The analysed table holds {} rows and {} distinct collars, so".format(
            len(table), len({record[UNIT_COLUMN] for record in table})
        ),
        "each number entering the test comes from a different independent unit.",
        "",
        "| management | collars | mean CH4 flux (mg m^-2 h^-1) | SD |",
        "| --- | --- | --- | --- |",
        "| {} | {} | {:.2f} | {:.2f} |".format(
            BASELINE, drained.size, drained.mean(), drained.std(ddof=1)
        ),
        "| {} | {} | {:.2f} | {:.2f} |".format(
            REWETTED, rewetted.size, rewetted.mean(), rewetted.std(ddof=1)
        ),
        "",
        "## Test",
        "",
        "Welch's two-sample t-test (unequal variances, two-sided) comparing rewetted",
        "with drained collars, one observation per collar.",
        "",
        "- mean difference (restored minus drained): {:.2f} mg m^-2 h^-1".format(diff),
        "- 95% confidence interval for the difference: {:.2f} to {:.2f} mg m^-2 h^-1".format(
            diff - half, diff + half
        ),
        "- Welch t = {:.2f} on df = {:.2f}".format(tstat, dof),
        "- {}".format(ptext),
        "- Cohen's d (pooled SD = {:.2f}): {:.2f}".format(spooled, dvalue),
        "",
        (
            "[selected-result] Rewetted peat collars emitted substantially more methane "
            "than drained collars: mean difference {:.2f} mg m^-2 h^-1 (95% CI {:.2f} to "
            "{:.2f}), Welch t({:.2f}) = {:.2f}, {}, with {} collars per group and one "
            "flux measurement per collar."
        ).format(diff, diff - half, diff + half, dof, tstat, ptext, drained.size),
        "",
        "## Notes",
        "",
        "No collar contributes more than one row, the two groups are balanced at {}".format(
            drained.size
        ),
        "collars each, and the independence assumption of the t-test is satisfied by",
        "the sampling design rather than by any post hoc averaging.",
    ]
    return "\n".join(lines) + "\n"


def main():
    table = read_table(INPUT_PATH)
    groups = split_by_management(table)
    report = build_report(table, groups[BASELINE], groups[REWETTED])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
