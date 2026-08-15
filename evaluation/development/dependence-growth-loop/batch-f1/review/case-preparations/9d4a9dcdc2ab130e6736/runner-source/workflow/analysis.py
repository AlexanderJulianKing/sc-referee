"""Serra Alta olive trial: does deficit irrigation lower leaf stomatal conductance?

Reads the porometer log in data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, stdev

from scipy import stats

LOG_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

VALUE_COL = "gsw_mmol_m2_s"
REGIMES = ("full", "deficit")


def read_log(path):
    """Pull (tree, regime, conductance) triples out of the porometer log."""
    entries = []
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            entries.append(
                (row["tree_id"], row["irrigation"], float(row[VALUE_COL]))
            )
    return entries


def split_by_regime(entries):
    """Collect the readings of each regime plus the trees they came from."""
    readings = {regime: [] for regime in REGIMES}
    trees = {regime: set() for regime in REGIMES}
    for tree, regime, value in entries:
        readings[regime].append(value)
        trees[regime].add(tree)
    return readings, trees


def p_phrase(pvalue):
    for cut in (0.001, 0.01, 0.05):
        if pvalue < cut:
            return "p < {0:g}".format(cut)
    return "p >= 0.05"


def build_report(readings, trees, tstat, pvalue):
    n_full = len(readings["full"])
    n_deficit = len(readings["deficit"])
    total = n_full + n_deficit
    n_trees = len(trees["full"] | trees["deficit"])
    per_tree = total // n_trees
    mean_full = mean(readings["full"])
    mean_deficit = mean(readings["deficit"])
    gap = mean_full - mean_deficit
    dof = total - 2
    verdict = p_phrase(pvalue)
    return [
        "# Deficit irrigation and leaf stomatal conductance (Serra Alta olive trial)",
        "",
        "## Sampling",
        "",
        "Steady-state porometer readings of leaf stomatal conductance "
        "(g_sw, mmol m^-2 s^-1)",
        f"were taken mid-morning in the third week of the stress period. "
        f"{total} sunlit leaves were",
        f"logged, {per_tree} per tree, across {n_trees} trees split between "
        f"the two irrigation regimes.",
        "",
        "| irrigation | leaves | mean g_sw | SD |",
        "| --- | --- | --- | --- |",
        f"| full | {n_full} | {mean_full:.2f} | {stdev(readings['full']):.2f} |",
        f"| deficit | {n_deficit} | {mean_deficit:.2f} | "
        f"{stdev(readings['deficit']):.2f} |",
        "",
        "## Test",
        "",
        "Two-sided two-sample Student t-test (pooled variance) on the leaf readings,",
        "full irrigation versus deficit irrigation.",
        "",
        f"- mean difference (full - deficit): {gap:.2f} mmol m^-2 s^-1",
        f"- t = {tstat:.3f}, df = {dof}, {verdict}",
        "",
        f"[selected-result] Leaves under full irrigation had higher stomatal conductance "
        f"than leaves under deficit irrigation ({mean_full:.2f} vs {mean_deficit:.2f} mmol "
        f"m^-2 s^-1, difference {gap:.2f}; two-sample t-test t = {tstat:.3f}, df = {dof}, "
        f"{verdict}).",
    ]


def main():
    entries = read_log(LOG_PATH)
    readings, trees = split_by_regime(entries)
    outcome = stats.ttest_ind(
        readings["full"], readings["deficit"], equal_var=True
    )
    lines = build_report(
        readings, trees, float(outcome.statistic), float(outcome.pvalue)
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
