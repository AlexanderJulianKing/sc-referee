"""Steady-state infiltration on restored hillside terraces, Kalu catchment.

Reads data/input.csv, compares biochar-amended sampling plots against
unamended sampling plots, and writes results/report.md.
"""

import csv
import math
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

RATE_COLUMN = "infiltration_mm_per_h"
GROUP_COLUMN = "treatment"
AMENDED = "biochar"
UNAMENDED = "none"


def read_plots(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def rates(plots, label):
    return [float(plot[RATE_COLUMN]) for plot in plots if plot[GROUP_COLUMN] == label]


def summarise(values):
    count = len(values)
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / (count - 1)
    return count, mean, math.sqrt(variance)


def welch_df(sd_one, n_one, sd_two, n_two):
    a = sd_one ** 2 / n_one
    b = sd_two ** 2 / n_two
    return (a + b) ** 2 / (a ** 2 / (n_one - 1) + b ** 2 / (n_two - 1))


def main():
    plots = read_plots(INPUT_PATH)
    n_total = len(plots)

    amended = rates(plots, AMENDED)
    unamended = rates(plots, UNAMENDED)

    n_a, mean_a, sd_a = summarise(amended)
    n_u, mean_u, sd_u = summarise(unamended)

    outcome = stats.ttest_ind(amended, unamended, equal_var=False)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    df = welch_df(sd_a, n_a, sd_u, n_u)

    p_text = "p < 0.001" if p_value < 0.001 else "p = {:.4f}".format(p_value)
    gap = mean_a - mean_u

    lines = [
        "# Biochar amendment and topsoil infiltration on restored hillside terraces",
        "",
        "## Question",
        "",
        "Ten restored hillside terraces in the Kalu catchment were surveyed after two wet",
        "seasons. Five terraces had received a biochar topsoil amendment; five received",
        "none. Field crews recorded steady-state infiltration with a double-ring",
        "infiltrometer at four sampling plots on every terrace. This report asks whether",
        "amended plots infiltrate faster than unamended plots.",
        "",
        "## Data",
        "",
        "- Sampling plots read from `data/input.csv`: {}".format(n_total),
        "- Biochar plots: {}, mean {:.2f} mm/h, SD {:.2f} mm/h".format(n_a, mean_a, sd_a),
        "- Unamended plots: {}, mean {:.2f} mm/h, SD {:.2f} mm/h".format(n_u, mean_u, sd_u),
        "- Mean difference (biochar minus none): {:.2f} mm/h".format(gap),
        "",
        "## Analysis",
        "",
        "Each of the {} plot measurements was entered as one observation and the two".format(n_total),
        "treatment groups were compared with a Welch two-sample t-test",
        "(`scipy.stats.ttest_ind`, `equal_var=False`), two-sided.",
        "",
        "## Result",
        "",
        "- Welch t = {:.2f}".format(t_stat),
        "- Approximate degrees of freedom = {:.2f}".format(df),
        "- Two-sided p-value: {}".format(p_text),
        "",
        (
            "[selected-result] Welch two-sample t-test on {} plot infiltration "
            "measurements: biochar-amended plots averaged {:.2f} mm/h higher than "
            "unamended plots ({:.2f} vs {:.2f} mm/h), t = {:.2f}, df = {:.2f}, {}."
        ).format(n_total, gap, mean_a, mean_u, t_stat, df, p_text),
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
