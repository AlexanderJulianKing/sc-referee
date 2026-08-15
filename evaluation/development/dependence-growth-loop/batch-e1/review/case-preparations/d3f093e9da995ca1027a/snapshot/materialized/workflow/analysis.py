"""Closed-chamber respirometry of Baetis mayfly nymphs from two elevation bands.

Reads data/input.csv, compares mass-specific metabolic rate between the lowland
and the highland band, and writes results/report.md.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

BAND_FIELD = "elevation_band"
NYMPH_FIELD = "nymph_id"
RATE_FIELD = "metabolic_rate_ul_o2_per_h_mg"
UNIT = "uL O2 per h per mg"


def read_runs(path):
    """Return every respirometry run in the file as a dict."""
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def band_rates(runs, band):
    return [float(run[RATE_FIELD]) for run in runs if run[BAND_FIELD] == band]


def band_nymphs(runs, band):
    return {run[NYMPH_FIELD] for run in runs if run[BAND_FIELD] == band}


def mean(values):
    return sum(values) / len(values)


def sum_squared_deviations(values):
    centre = mean(values)
    return sum((value - centre) ** 2 for value in values)


def build_report(runs):
    low = band_rates(runs, "lowland")
    high = band_rates(runs, "highland")
    low_nymphs = band_nymphs(runs, "lowland")
    high_nymphs = band_nymphs(runs, "highland")

    dof = len(low) + len(high) - 2
    pooled_sd = math.sqrt(
        (sum_squared_deviations(low) + sum_squared_deviations(high)) / dof
    )
    difference = mean(high) - mean(low)
    outcome = stats.ttest_ind(high, low, equal_var=True)

    lines = [
        "# Metabolic rate of Baetis nymphs across two elevation bands",
        "",
        "## Data",
        "",
        f"Source: {INPUT_PATH.as_posix()}, {len(runs)} rows. Each row is one closed-chamber",
        f"respirometry run. {len(low_nymphs | high_nymphs)} nymphs were collected and each was run twice on",
        "consecutive mornings.",
        "",
        f"| elevation band | runs | nymphs | mean rate ({UNIT}) |",
        "| --- | --- | --- | --- |",
        f"| lowland | {len(low)} | {len(low_nymphs)} | {mean(low):.2f} |",
        f"| highland | {len(high)} | {len(high_nymphs)} | {mean(high):.2f} |",
        "",
        "## Analysis",
        "",
        f"All {len(runs)} runs were entered as individual observations in a two-sample",
        "Student t-test (equal variances assumed, scipy.stats.ttest_ind) comparing",
        f"highland runs with lowland runs. Pooled standard deviation {pooled_sd:.3f} {UNIT}",
        f"on {dof} degrees of freedom.",
        "",
        "## Result",
        "",
        f"Mean difference (highland minus lowland): {difference:.2f} {UNIT}.",
        f"t({dof}) = {outcome.statistic:.4f}, two-sided p = {outcome.pvalue:.4f}.",
        "",
        f"[selected-result] Two-sample Student t-test on {len(runs)} respirometry runs: "
        f"highland nymphs have a higher mass-specific metabolic rate than lowland "
        f"nymphs by {difference:.2f} {UNIT} (t({dof}) = {outcome.statistic:.4f}, "
        f"two-sided p = {outcome.pvalue:.4f}).",
    ]
    return "\n".join(lines) + "\n"


def main():
    runs = read_runs(INPUT_PATH)
    report = build_report(runs)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
