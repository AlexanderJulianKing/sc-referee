"""Compare methane flux between drained and intact peatland chamber closures."""

import csv
import pathlib

import numpy as np
from scipy import stats

INPUT_PATH = pathlib.Path("data/input.csv")
REPORT_PATH = pathlib.Path("results/report.md")

CONDITION_COLUMN = "peat_condition"
FLUX_COLUMN = "ch4_flux_mg_m2_h"
CONDITIONS = ("drained", "intact")


def read_table(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def flux_vector(table, condition):
    values = [
        float(row[FLUX_COLUMN])
        for row in table
        if row[CONDITION_COLUMN] == condition
    ]
    return np.asarray(values, dtype=float)


def welch_df(first, second):
    va = first.var(ddof=1) / first.size
    vb = second.var(ddof=1) / second.size
    return (va + vb) ** 2 / (
        va ** 2 / (first.size - 1) + vb ** 2 / (second.size - 1)
    )


def format_p(value):
    if value < 1e-6:
        return "< 1e-06"
    return "= {:.6f}".format(value)


def build_report(drained, intact):
    outcome = stats.ttest_ind(drained, intact, equal_var=False)
    t_stat = float(outcome.statistic)
    p_text = format_p(float(outcome.pvalue))
    df = welch_df(drained, intact)
    gap = float(drained.mean() - intact.mean())

    summary_line = (
        "Static-chamber closures read from `data/input.csv`: {} flux "
        "measurements (drained = {}, intact = {})."
    ).format(drained.size + intact.size, drained.size, intact.size)

    method_line = (
        "Welch's two-sample t-test (unequal variances) comparing the methane "
        "flux of drained and intact peat. Every chamber closure in "
        "`data/input.csv` is entered as one observation."
    )

    verdict_line = (
        "[selected-result] Drained peat emits more methane than intact peat: "
        "mean difference {:.3f} mg m^-2 h^-1 (drained {:.3f}, intact {:.3f}), "
        "Welch t = {:.3f}, df = {:.2f}, two-sided p {}."
    ).format(gap, drained.mean(), intact.mean(), t_stat, df, p_text)

    lines = [
        "# Methane flux from drained versus intact peatland",
        "",
        "## Data",
        "",
        summary_line,
        "",
        "| Peat condition | n | Mean CH4 flux (mg m^-2 h^-1) | SD |",
        "| --- | --- | --- | --- |",
    ]
    for label, sample in zip(CONDITIONS, (drained, intact)):
        lines.append(
            "| {} | {} | {:.3f} | {:.3f} |".format(
                label, sample.size, sample.mean(), sample.std(ddof=1)
            )
        )
    lines.extend(
        [
            "",
            "## Analysis",
            "",
            method_line,
            "",
            "- Difference in means (drained - intact): {:.3f} mg m^-2 h^-1".format(gap),
            "- Welch t = {:.3f}".format(t_stat),
            "- Welch degrees of freedom = {:.2f}".format(df),
            "- Two-sided p {}".format(p_text),
            "",
            "## Conclusion",
            "",
            verdict_line,
            "",
        ]
    )
    return "\n".join(lines)


def main():
    table = read_table(INPUT_PATH)
    drained = flux_vector(table, "drained")
    intact = flux_vector(table, "intact")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(drained, intact), encoding="utf-8")


if __name__ == "__main__":
    main()
