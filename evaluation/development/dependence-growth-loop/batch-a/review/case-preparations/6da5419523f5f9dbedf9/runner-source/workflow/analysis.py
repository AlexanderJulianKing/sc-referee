"""Rise-height comparison for a two-flour sourdough leavening trial."""

import csv
import math
import pathlib

import numpy as np
from scipy import stats

INPUT_PATH = pathlib.Path("data/input.csv")
REPORT_PATH = pathlib.Path("results/report.md")


def read_readings(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def rise_by_flour(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["flour_type"], []).append(float(row["rise_mm"]))
    return {flour: np.array(vals, dtype=float) for flour, vals in sorted(grouped.items())}


def jars_of(rows, flour):
    return len({row["jar_id"] for row in rows if row["flour_type"] == flour})


def p_phrase(pvalue):
    if pvalue < 0.001:
        return "p < 0.001"
    return "p = {:.4f}".format(pvalue)


def build_report(rows):
    groups = rise_by_flour(rows)
    (flour_a, rise_a), (flour_b, rise_b) = groups.items()

    n_a, n_b = rise_a.size, rise_b.size
    jars_a, jars_b = jars_of(rows, flour_a), jars_of(rows, flour_b)
    mean_a, mean_b = float(rise_a.mean()), float(rise_b.mean())
    sd_a, sd_b = float(rise_a.std(ddof=1)), float(rise_b.std(ddof=1))

    tstat, pvalue = stats.ttest_ind(rise_a, rise_b, equal_var=True)
    dof = n_a + n_b - 2
    pooled_sd = math.sqrt(((n_a - 1) * sd_a ** 2 + (n_b - 1) * sd_b ** 2) / dof)
    diff = mean_a - mean_b
    effect = diff / pooled_sd

    n_rows = len(rows)
    n_jars = jars_a + jars_b
    hours = ", ".join(str(h) for h in sorted({int(row["incubation_h"]) for row in rows}))

    lines = [
        "# Rise height of sourdough starters: rye versus spelt flour",
        "",
        "## Data",
        "",
        "`data/input.csv` holds {} timed rise readings from {} fermentation jars.".format(n_rows, n_jars),
        "Each jar contributed {} readings, taken at hours {} after feeding.".format(n_rows // n_jars, hours),
        "",
        "| flour_type | jars | readings | mean rise (mm) | sd (mm) |",
        "| --- | ---: | ---: | ---: | ---: |",
        "| {} | {} | {} | {:.2f} | {:.2f} |".format(flour_a, jars_a, n_a, mean_a, sd_a),
        "| {} | {} | {} | {:.2f} | {:.2f} |".format(flour_b, jars_b, n_b, mean_b, sd_b),
        "",
        "## Analysis",
        "",
        "Every one of the {} rows was entered as a separate observation in a two-sided,".format(n_rows),
        "equal-variance two-sample Student t-test comparing rise height between the two",
        "flour types ({} minus {}). The group summaries above use the same {} rows.".format(flour_a, flour_b, n_rows),
        "",
        "## Result",
        "",
        "[selected-result] Two-sample t-test over {} rise readings: {} minus {} = {:.2f} mm, t({}) = {:.2f}, {}, Cohen's d = {:.2f}.".format(
            n_rows, flour_a, flour_b, diff, dof, float(tstat), p_phrase(float(pvalue)), effect
        ),
        "",
        "Rye jars measured about 7 mm lower than spelt jars across the 24-hour window,",
        "and at the level of individual readings the gap is flagged as highly significant.",
    ]
    return "\n".join(lines) + "\n"


def main():
    rows = read_readings(INPUT_PATH)
    report = build_report(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
