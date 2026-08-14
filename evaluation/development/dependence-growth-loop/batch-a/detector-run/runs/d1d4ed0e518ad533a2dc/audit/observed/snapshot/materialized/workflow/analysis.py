"""Free chlorine residual in North Ridge service reservoirs.

Reads data/input.csv and writes results/report.md.
"""

import csv
from pathlib import Path

import numpy as np
from scipy import stats

SOURCE = Path("data/input.csv")
REPORT = Path("results/report.md")
GROUP_COL = "liner_type"
VALUE_COL = "free_chlorine_mgl"
EPOXY = "epoxy"
CEMENT = "cement-mortar"


def read_groups(path):
    buckets = {EPOXY: [], CEMENT: []}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            buckets[record[GROUP_COL]].append(float(record[VALUE_COL]))
    return {key: np.asarray(vals, dtype=float) for key, vals in buckets.items()}


def welch_dof(first, second):
    a = float(np.var(first, ddof=1)) / first.size
    b = float(np.var(second, ddof=1)) / second.size
    return (a + b) ** 2 / (a * a / (first.size - 1) + b * b / (second.size - 1))


def summary_row(label, values):
    return "| {} | {} | {:.3f} | {:.3f} |".format(
        label, values.size, float(np.mean(values)), float(np.std(values, ddof=1))
    )


def compose(groups):
    epoxy = groups[EPOXY]
    cement = groups[CEMENT]
    total = epoxy.size + cement.size
    outcome = stats.ttest_ind(epoxy, cement, equal_var=False)
    tstat = float(outcome.statistic)
    pval = float(outcome.pvalue)
    dof = welch_dof(epoxy, cement)
    diff = float(np.mean(epoxy)) - float(np.mean(cement))
    ptext = "p < 0.001" if pval < 0.001 else "p = {:.3f}".format(pval)
    lines = [
        "# Free chlorine residual by reservoir liner type",
        "",
        "## Data",
        "",
        "Twelve municipal service reservoirs in the North Ridge distribution zone were",
        "sampled during a single spring flushing window. Six carry an epoxy liner and",
        "six carry a cement-mortar liner. Each reservoir was tapped at four fixed port",
        "depths (1.5, 3.0, 4.5 and 6.0 m), giving {} free chlorine readings in".format(total),
        "`data/input.csv`.",
        "",
        "## Analysis",
        "",
        "Each reading was entered as one observation and the two liner groups were",
        "compared with a two-sided Welch two-sample t-test (unequal variances).",
        "",
        "| liner | samples | mean free chlorine (mg/L) | SD (mg/L) |",
        "| --- | ---: | ---: | ---: |",
        summary_row(EPOXY, epoxy),
        summary_row(CEMENT, cement),
        "",
        "Mean difference (epoxy minus cement-mortar): {:.3f} mg/L".format(diff),
        "",
        "Welch t = {:.3f}, df = {:.1f}, {}".format(tstat, dof, ptext),
        "",
        "## Result",
        "",
        (
            "[selected-result] Epoxy-lined reservoirs carried {:.3f} mg/L more free "
            "chlorine than cement-mortar-lined reservoirs (two-sided Welch two-sample "
            "t-test over {} readings, {} per liner: t = {:.3f}, df = {:.1f}, {})."
        ).format(diff, total, epoxy.size, tstat, dof, ptext),
    ]
    return "\n".join(lines) + "\n"


def main():
    groups = read_groups(SOURCE)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(compose(groups), encoding="utf-8")


if __name__ == "__main__":
    main()
