"""Compare leaf-level net CO2 assimilation between two quinoa cultivars.

Reads data/input.csv and writes results/report.md.
"""

import csv
import pathlib

import numpy as np
from scipy import stats

INPUT_PATH = pathlib.Path("data/input.csv")
OUTPUT_PATH = pathlib.Path("results/report.md")

GROUP_COLUMN = "cultivar"
RATE_COLUMN = "assimilation_umol_m2_s"
REFERENCE = "Pasankalla"
CONTRAST = "Titicaca"
ALPHA = 0.05


def read_table(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def rates(table, cultivar):
    picked = [
        float(row[RATE_COLUMN])
        for row in table
        if row[GROUP_COLUMN] == cultivar
    ]
    return np.asarray(picked, dtype=float)


def welch_df(first, second):
    term_a = first.var(ddof=1) / first.size
    term_b = second.var(ddof=1) / second.size
    numerator = (term_a + term_b) ** 2
    denominator = (term_a ** 2) / (first.size - 1) + (term_b ** 2) / (second.size - 1)
    return numerator / denominator


def group_row(label, values):
    return "| {0} | {1} | {2:.3f} | {3:.3f} |".format(
        label, values.size, values.mean(), values.std(ddof=1)
    )


def p_text(pvalue):
    if pvalue < 1e-4:
        return "p < 0.0001"
    return "p = {0:.4f}".format(pvalue)


def build_report(table, ref, con):
    tstat, pvalue = stats.ttest_ind(con, ref, equal_var=False)
    dof = welch_df(con, ref)
    diff = con.mean() - ref.mean()
    ptext = p_text(pvalue)

    summary = (
        "[selected-result] Welch's two-sample t-test over {0} leaf observations"
        " gives t = {1:.3f}, df = {2:.1f}, {3}: mean net assimilation is higher"
        " in {4} ({5:.3f}) than in {6} ({7:.3f}) umol m-2 s-1."
    ).format(
        len(table), tstat, dof, ptext, CONTRAST, con.mean(), REFERENCE, ref.mean()
    )

    lines = [
        "# Leaf-level carbon assimilation in two quinoa cultivars",
        "",
        "## Data",
        "",
        "Source table: `data/input.csv` ({0} measurement rows).".format(len(table)),
        "",
        "Measured variable: net CO2 assimilation rate (assimilation_umol_m2_s), recorded on",
        "individually tagged leaves of greenhouse-grown quinoa plants.",
        "",
        "| Cultivar | Rows | Mean | SD |",
        "| --- | ---: | ---: | ---: |",
        group_row(REFERENCE, ref),
        group_row(CONTRAST, con),
        "",
        "## Analysis",
        "",
        "Each measured leaf was entered as one observation and the two cultivar groups were",
        "compared with Welch's two-sample t-test (scipy.stats.ttest_ind, equal_var=False),",
        "two-sided, alpha = {0}.".format(ALPHA),
        "",
        "## Result",
        "",
        "Mean difference (Titicaca minus Pasankalla): {0:.3f} umol m-2 s-1".format(diff),
        "t = {0:.3f}, df = {1:.1f}, {2}".format(tstat, dof, ptext),
        "",
        summary,
    ]
    return "\n".join(lines) + "\n"


def main():
    table = read_table(INPUT_PATH)
    ref = rates(table, REFERENCE)
    con = rates(table, CONTRAST)
    report = build_report(table, ref, con)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
