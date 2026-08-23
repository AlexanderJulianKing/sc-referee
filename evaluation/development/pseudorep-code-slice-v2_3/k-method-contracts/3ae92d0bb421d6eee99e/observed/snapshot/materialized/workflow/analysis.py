"""Karhusuo peat complex: chamber CH4 flux under two water-table regimes.

Reads data/input.csv, compares the drained and rewetted sectors, and
writes results/report.md.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

REGIME_COL = "water_table_regime"
FLUX_COL = "ch4_flux_mg_m2_h"


def read_records(path):
    with path.open("r", newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def flux_samples(records):
    pooled = defaultdict(list)
    for record in records:
        pooled[record[REGIME_COL].strip()].append(float(record[FLUX_COL]))
    return {key: np.array(values, dtype=float) for key, values in pooled.items()}


def moments(sample):
    return int(sample.size), float(np.mean(sample)), float(np.std(sample, ddof=1))


def p_phrase(pvalue):
    if pvalue < 1e-4:
        return "p < 0.0001"
    return "p = {:.4f}".format(pvalue)


def main():
    samples = flux_samples(read_records(INPUT_PATH))
    drained = samples["drained"]
    rewetted = samples["rewetted"]

    n_dr, mean_dr, sd_dr = moments(drained)
    n_rw, mean_rw, sd_rw = moments(rewetted)
    contrast = mean_rw - mean_dr

    outcome = stats.ttest_ind(rewetted, drained, equal_var=True)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)
    df = n_rw + n_dr - 2

    headline = (
        "[selected-result] Rewetted chamber flux exceeds drained by "
        "{:.2f} mg m-2 h-1 (rewetted mean {:.2f}, drained mean {:.2f}); "
        "two-sample Student t-test on the {:d} individual chamber "
        "readings, t({:d}) = {:.2f}, {}."
    ).format(contrast, mean_rw, mean_dr, n_rw + n_dr, df, tstat, p_phrase(pvalue))

    lines = [
        "# Rewetting and CH4 flux at the Karhusuo peat complex",
        "",
        "## What was measured",
        "",
        "Static closed-chamber CH4 flux was logged in the drained and rewetted",
        "sectors of the Karhusuo peat complex over the 2024 growing season.",
        "",
        "| water table regime | measurements | mean CH4 flux (mg m-2 h-1) | SD |",
        "| --- | ---: | ---: | ---: |",
        "| drained | {:d} | {:.2f} | {:.3f} |".format(n_dr, mean_dr, sd_dr),
        "| rewetted | {:d} | {:.2f} | {:.3f} |".format(n_rw, mean_rw, sd_rw),
        "",
        "## Test",
        "",
        "Two-sample Student t-test (pooled variance) on the chamber flux",
        "readings, rewetted against drained.",
        "",
        headline,
        "",
        "## Note",
        "",
        "The pooled-variance form was kept because the two sector spreads were",
        "nearly identical (SD {:.3f} drained vs {:.3f} rewetted).".format(sd_dr, sd_rw),
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
