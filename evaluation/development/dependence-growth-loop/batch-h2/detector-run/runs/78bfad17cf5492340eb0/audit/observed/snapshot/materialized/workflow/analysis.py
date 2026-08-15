"""Coated vs. bare photovoltaic modules: soiling-induced power loss.

Reads the weekly inspection export and writes the trial report.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

TREATED = "nanocoat"
CONTROL = "bare"


def read_inspections(path):
    """Load every inspection record from the trial export."""
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def module_ids_in_order(records):
    """Module labels in the order they first appear in the export."""
    ordered = []
    for row in records:
        if row["module_id"] not in ordered:
            ordered.append(row["module_id"])
    return ordered


def losses(records, coating=None, module_id=None):
    """Power-loss readings, optionally restricted to a coating or a module."""
    picked = []
    for row in records:
        if coating is not None and row["coating"] != coating:
            continue
        if module_id is not None and row["module_id"] != module_id:
            continue
        picked.append(float(row["power_loss_pct"]))
    return picked


def coating_of(records, module_id):
    for row in records:
        if row["module_id"] == module_id:
            return row["coating"]
    raise KeyError(module_id)


def p_phrase(pvalue):
    if pvalue < 0.001:
        return "p < 0.001"
    return "p = {0:.3f}".format(pvalue)


def build_report(records):
    treated = losses(records, coating=TREATED)
    control = losses(records, coating=CONTROL)

    outcome = stats.ttest_ind(treated, control, equal_var=True)
    tstat = float(outcome.statistic)
    pval = float(outcome.pvalue)
    dof = len(treated) + len(control) - 2

    treated_mean = statistics.fmean(treated)
    control_mean = statistics.fmean(control)
    gap = treated_mean - control_mean
    n_rows = len(records)

    out = []
    out.append(
        "# Soiling-Induced Power Loss in Coated and Bare Photovoltaic Modules")
    out.append("")
    out.append("## Data")
    out.append("")
    out.append(
        "Field trial at one utility-scale array: 12 modules (6 treated with"
        " the nanocoat")
    out.append(
        "anti-soiling layer, 6 bare controls) were inspected once per week"
        " for 5")
    out.append(
        "consecutive weeks, yielding {0} inspection records. The response"
        " variable is".format(n_rows))
    out.append(
        "the soiling-induced power loss relative to a clean-module reference,"
        " in percent.")
    out.append("")
    out.append("## Per-module mean power loss")
    out.append("")
    out.append("| module_id | coating | inspections | mean loss (%) |")
    out.append("| --- | --- | --- | --- |")
    for module in module_ids_in_order(records):
        vals = losses(records, module_id=module)
        out.append("| {0} | {1} | {2} | {3:.3f} |".format(
            module, coating_of(records, module), len(vals),
            statistics.fmean(vals)))
    out.append("")
    out.append("## Group summary")
    out.append("")
    out.append("| coating | inspection records | mean (%) | SD (%) |")
    out.append("| --- | --- | --- | --- |")
    out.append("| {0} | {1} | {2:.3f} | {3:.3f} |".format(
        TREATED, len(treated), treated_mean, statistics.stdev(treated)))
    out.append("| {0} | {1} | {2:.3f} | {3:.3f} |".format(
        CONTROL, len(control), control_mean, statistics.stdev(control)))
    out.append("")
    out.append("## Test")
    out.append("")
    out.append(
        "Two-sample Student t-test (equal variances assumed) comparing"
        " nanocoat against")
    out.append(
        "bare power-loss values, with each of the {0} inspection records"
        " entered as one".format(n_rows))
    out.append("independent observation.")
    out.append("")
    out.append(
        "- Mean difference (nanocoat minus bare): {0:.3f} percentage"
        " points".format(gap))
    out.append("- t({0}) = {1:.3f}, {2}".format(dof, tstat, p_phrase(pval)))
    out.append("")
    out.append(
        "[selected-result] Two-sample Student t-test over {0} weekly"
        " inspection records: nanocoat modules averaged {1:.3f}% soiling"
        " power loss versus {2:.3f}% for bare modules, a difference of"
        " {3:.3f} percentage points (t({4}) = {5:.3f}, {6}).".format(
            n_rows, treated_mean, control_mean, gap, dof, tstat,
            p_phrase(pval)))
    return "\n".join(out) + "\n"


def main():
    records = read_inspections(INPUT_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_report(records), encoding="utf-8")


if __name__ == "__main__":
    main()
