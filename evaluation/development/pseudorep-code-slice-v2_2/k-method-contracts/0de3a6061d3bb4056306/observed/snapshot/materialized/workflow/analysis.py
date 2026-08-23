"""Compare chamber methane flux between restored and drained peatland plots.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
GROUP_COLUMN = "management"
FLUX_COLUMN = "ch4_flux_mg_m2_h"
GROUP_ORDER = ("restored", "drained")


def read_measurements(path):
    """Return every CSV record as a dictionary keyed by column name."""
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def flux_by_group(rows):
    """Collect the flux readings belonging to each management class."""
    grouped = {name: [] for name in GROUP_ORDER}
    for row in rows:
        grouped[row[GROUP_COLUMN]].append(float(row[FLUX_COLUMN]))
    return grouped


def summarise(values):
    """Count, mean and sample standard deviation of one list of readings."""
    count = len(values)
    mean = math.fsum(values) / count
    variance = math.fsum((value - mean) ** 2 for value in values) / (count - 1)
    return count, mean, math.sqrt(variance)


def format_p(p_value):
    if p_value < 0.001:
        return "p < 0.001"
    return "p = {0:.3f}".format(p_value)


def compose(rows):
    """Build the full text of the report."""
    grouped = flux_by_group(rows)
    per_group = {name: summarise(grouped[name]) for name in GROUP_ORDER}
    n_res, mean_res, sd_res = per_group["restored"]
    n_dra, mean_dra, sd_dra = per_group["drained"]

    outcome = stats.ttest_ind(
        grouped["restored"], grouped["drained"], equal_var=True
    )
    dof = n_res + n_dra - 2
    pooled_sd = math.sqrt(
        ((n_res - 1) * sd_res ** 2 + (n_dra - 1) * sd_dra ** 2) / dof
    )
    effect = (mean_res - mean_dra) / pooled_sd

    table = [
        "| management | measurements | mean flux (mg CH4 m^-2 h^-1) | SD |",
        "| --- | --- | --- | --- |",
    ]
    for name in GROUP_ORDER:
        count, mean, sd = per_group[name]
        table.append(
            "| {0} | {1} | {2:.2f} | {3:.2f} |".format(name, count, mean, sd)
        )

    lines = [
        "# Methane flux in restored versus drained peatland chambers",
        "",
        "## Data",
        "",
        "The file `data/input.csv` records {0} static-chamber measurements of methane"
        " flux (mg CH4 m^-2 h^-1) from a lowland peatland restoration trial, together"
        " with the management class of the chamber's plot, the survey visit, and the"
        " water-table depth logged at sampling.".format(len(rows)),
        "",
        "## Analysis",
        "",
        "Flux readings were summarised per management class and compared with a"
        " two-sample Student t-test (scipy.stats.ttest_ind, equal variances assumed)"
        " in which each of the {0} measurement rows entered the test as one"
        " observation. Cohen's d was computed from the pooled standard"
        " deviation.".format(len(rows)),
        "",
        "## Summary statistics",
        "",
    ]
    lines.extend(table)
    lines.extend(
        [
            "",
            "## Result",
            "",
            "[selected-result] Restored chambers released more methane than drained"
            " chambers: mean difference {0:.2f} mg CH4 m^-2 h^-1 (restored {1:.2f},"
            " drained {2:.2f}), two-sample t-test t({3}) = {4:.2f}, {5}, Cohen's"
            " d = {6:.2f}.".format(
                mean_res - mean_dra,
                mean_res,
                mean_dra,
                dof,
                float(outcome.statistic),
                format_p(float(outcome.pvalue)),
                effect,
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    rows = read_measurements(INPUT_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(compose(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
