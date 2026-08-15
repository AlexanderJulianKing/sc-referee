"""Kettle Fen rewetting trial: static-chamber methane flux comparison."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

FLUX_FIELD = "ch4_flux_mg_m2_h"
REWETTED = "rewetted"
DRAINED = "drained"


def read_table(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def fluxes_for(table, treatment):
    return [float(row[FLUX_FIELD]) for row in table if row["treatment"] == treatment]


def plot_ids_for(table, treatment):
    return sorted({row["plot_id"] for row in table if row["treatment"] == treatment})


def render(table):
    wet = fluxes_for(table, REWETTED)
    dry = fluxes_for(table, DRAINED)
    wet_plots = plot_ids_for(table, REWETTED)
    dry_plots = plot_ids_for(table, DRAINED)
    rounds = sorted({row["survey_round"] for row in table})

    wet_mean, dry_mean = statistics.fmean(wet), statistics.fmean(dry)
    wet_sd, dry_sd = statistics.stdev(wet), statistics.stdev(dry)
    gap = wet_mean - dry_mean

    outcome = stats.ttest_ind(wet, dry, equal_var=True)
    dof = len(wet) + len(dry) - 2
    p_text = "< 0.001" if outcome.pvalue < 0.001 else "= {:.3f}".format(outcome.pvalue)

    headline = (
        "[selected-result] Mean chamber methane flux was higher under rewetting"
        " than under drainage ({:.2f} vs {:.2f} mg m-2 h-1; difference"
        " {:.2f} mg m-2 h-1), two-sample Student t test on all {} readings,"
        " t({}) = {:.3f}, p {}."
    ).format(wet_mean, dry_mean, gap, len(table), dof, outcome.statistic, p_text)

    lines = [
        "# Methane flux response to peatland rewetting",
        "",
        "## Data",
        "",
        "`data/input.csv` holds {} static-chamber methane flux readings from the".format(
            len(table)
        ),
        "Kettle Fen restoration trial: {} chamber plots ({} rewetted, {} drained),".format(
            len(wet_plots) + len(dry_plots), len(wet_plots), len(dry_plots)
        ),
        "each visited on {} survey rounds.".format(len(rounds)),
        "",
        "| Treatment | Readings | Mean CH4 flux (mg m-2 h-1) | SD |",
        "| --- | --- | --- | --- |",
        "| rewetted | {} | {:.2f} | {:.3f} |".format(len(wet), wet_mean, wet_sd),
        "| drained | {} | {:.2f} | {:.3f} |".format(len(dry), dry_mean, dry_sd),
        "",
        "## Analysis",
        "",
        "A two-sample Student t test (equal variances assumed) compared rewetted",
        "against drained flux readings. Every reading in the file was entered as a",
        "separate observation in the test.",
        "",
        "- Mean difference (rewetted - drained): {:.2f} mg m-2 h-1".format(gap),
        "- t({}) = {:.3f}".format(dof, outcome.statistic),
        "- Two-sided p {}".format(p_text),
        "",
        headline,
        "",
        "## Notes",
        "",
        "Fluxes are milligrams of CH4 per square metre per hour. No reading was",
        "excluded and no value was transformed.",
    ]
    return "\n".join(lines) + "\n"


def main():
    table = read_table(INPUT_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render(table), encoding="utf-8")


if __name__ == "__main__":
    main()
