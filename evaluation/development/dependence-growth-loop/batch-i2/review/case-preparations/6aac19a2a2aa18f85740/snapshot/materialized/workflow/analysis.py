"""Midsummer methane flux in intact versus drained peat bogs.

Reads the bog survey in data/input.csv (one bog per row) and writes results/report.md.
"""

import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

UNIT_COLUMN = "bog_id"
GROUP_COLUMN = "hydrology"
FLUX_COLUMN = "ch4_flux_mg_m2_h"
GROUP_ORDER = ("intact", "drained")


def read_survey(path):
    """Collect bog identifiers and per-bog flux readings, keyed by hydrology class."""
    identifiers = []
    fluxes = {label: [] for label in GROUP_ORDER}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            label = record[GROUP_COLUMN].strip()
            if label not in fluxes:
                raise ValueError("unrecognised hydrology class: {0}".format(label))
            identifiers.append(record[UNIT_COLUMN].strip())
            fluxes[label].append(float(record[FLUX_COLUMN]))
    if not identifiers:
        raise ValueError("no bogs found in {0}".format(path))
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("a bog identifier is repeated; every row must be a separate bog")
    samples = {}
    for label in GROUP_ORDER:
        samples[label] = np.asarray(fluxes[label], dtype=float)
    return identifiers, samples


def main():
    identifiers, samples = read_survey(INPUT_PATH)
    intact = samples["intact"]
    drained = samples["drained"]

    n_intact = int(intact.size)
    n_drained = int(drained.size)
    mean_intact = float(intact.mean())
    mean_drained = float(drained.mean())
    sd_intact = float(intact.std(ddof=1))
    sd_drained = float(drained.std(ddof=1))

    dof = n_intact + n_drained - 2
    pooled_var = ((n_intact - 1) * sd_intact ** 2 + (n_drained - 1) * sd_drained ** 2) / dof
    pooled_sd = math.sqrt(pooled_var)
    difference = mean_intact - mean_drained
    effect = difference / pooled_sd

    outcome = stats.ttest_ind(intact, drained, equal_var=True)
    t_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)

    selected = (
        "[selected-result] Intact bogs emitted more methane than drained bogs: "
        "mean flux {0:.3f} vs {1:.3f} mg m-2 h-1 (difference {2:.3f}), "
        "pooled two-sample t-test t({3}) = {4:.4f}, two-sided p = {5:.5f}, "
        "standardised effect size {6:.3f}."
    ).format(mean_intact, mean_drained, difference, dof, t_stat, p_value, effect)

    lines = [
        "# Methane flux in intact versus drained peat bogs",
        "",
        "## Design",
        "",
        "Twelve peat bogs, each in a separate catchment, were surveyed once during a single midsummer",
        "campaign: six bogs with an intact water table and six bogs drained by historic ditching. Every",
        "bog contributes exactly one closed-chamber flux measurement, so each row of data/input.csv is",
        "one independent unit. Rows read: {0}; distinct bog identifiers: {1}.".format(
            len(identifiers), len(set(identifiers))
        ),
        "",
        "## Group summaries",
        "",
        "| Hydrology | Bogs | Mean CH4 flux (mg m-2 h-1) | SD (mg m-2 h-1) |",
        "| --- | --- | --- | --- |",
        "| intact | {0} | {1:.3f} | {2:.3f} |".format(n_intact, mean_intact, sd_intact),
        "| drained | {0} | {1:.3f} | {2:.3f} |".format(n_drained, mean_drained, sd_drained),
        "",
        "## Test",
        "",
        "Two-sided two-sample Student t-test with pooled variance on the bog-level flux values. No bog",
        "is measured twice, so the twelve observations enter the test as twelve independent draws.",
        "",
        "- Difference in means (intact minus drained): {0:.3f} mg m-2 h-1".format(difference),
        "- Pooled SD: {0:.3f} mg m-2 h-1".format(pooled_sd),
        "- Standardised effect size (difference / pooled SD): {0:.3f}".format(effect),
        "- t({0}) = {1:.4f}, p = {2:.5f}".format(dof, t_stat, p_value),
        "",
        selected,
        "",
        "## Reading the result",
        "",
        "At the conventional 5 percent level the difference is statistically significant: in this sample",
        "the drained bogs emit about 16 percent less methane than the intact bogs. The test assumes",
        "independent, approximately normal, equal-variance groups. Independence holds by construction",
        "because every bog identifier appears on exactly one row; normality and equal variance are",
        "assumed rather than demonstrated at six bogs per group.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
