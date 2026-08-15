"""Infiltration gain in compost-amended rain gardens.

Reads data/input.csv, which stores one row per infiltrometer visit, collapses
the repeated visits of each garden into a single garden-level gain, and writes
results/report.md.
"""

from __future__ import annotations

import csv
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")
UNIT_COLUMN = "garden_id"
AMENDED_COLUMN = "amended_mm_per_h"
REFERENCE_COLUMN = "reference_mm_per_h"
NULL_GAIN = 0.0
CONF_LEVEL = 0.95


@dataclass
class Garden:
    """One retrofitted rain garden: the independent unit of this study."""

    garden_id: str
    session_gains: list = field(default_factory=list)

    def add_session(self, amended, reference):
        self.session_gains.append(amended - reference)

    @property
    def n_sessions(self):
        return len(self.session_gains)

    @property
    def mean_gain(self):
        return statistics.fmean(self.session_gains)


def collect_gardens(path):
    """Group the visit rows by garden, keeping first-seen garden order."""
    gardens = {}
    n_rows = 0
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            n_rows += 1
            label = row[UNIT_COLUMN]
            if label not in gardens:
                gardens[label] = Garden(label)
            gardens[label].add_session(
                float(row[AMENDED_COLUMN]), float(row[REFERENCE_COLUMN])
            )
    return list(gardens.values()), n_rows


def format_p(pvalue):
    for cut in (0.0001, 0.001, 0.01):
        if pvalue < cut:
            return "p < {0:g}".format(cut)
    return "p = {0:.3f}".format(pvalue)


def build_report(gardens, n_rows):
    unit_means = [garden.mean_gain for garden in gardens]
    session_counts = [garden.n_sessions for garden in gardens]
    n_units = len(unit_means)
    df = n_units - 1
    mean_gain = statistics.fmean(unit_means)
    sd_gain = statistics.stdev(unit_means)
    se_gain = sd_gain / math.sqrt(n_units)
    tstat, pvalue = stats.ttest_1samp(unit_means, NULL_GAIN)
    margin = float(stats.t.ppf(0.5 + CONF_LEVEL / 2.0, df)) * se_gain
    low = mean_gain - margin
    high = mean_gain + margin
    p_text = format_p(float(pvalue))

    lines = []
    lines.append("# Infiltration gain in compost-amended rain gardens")
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append("Source table: `data/input.csv`")
    lines.append("")
    lines.append(
        "The file holds {0} infiltrometer survey sessions recorded at {1} rain"
        " gardens, with {2} to {3} sessions per garden (mean {4:.2f}). Each"
        " session pairs one measurement in the compost-amended cell with one"
        " measurement in the untreated reference cell of the same garden; the"
        " session gain is amended minus reference, in mm/h.".format(
            n_rows,
            n_units,
            min(session_counts),
            max(session_counts),
            statistics.fmean(session_counts),
        )
    )
    lines.append("")
    lines.append(
        "Sessions repeated at the same garden are not independent of one"
        " another, so the session gains are averaged within each garden before"
        " testing. The reported test therefore uses {0} garden means, one"
        " analysed value per independent garden.".format(n_units)
    )
    lines.append("")
    lines.append("## Per-garden means")
    lines.append("")
    lines.append("| garden_id | sessions | mean gain (mm/h) |")
    lines.append("| --- | --- | --- |")
    for garden in gardens:
        lines.append(
            "| {0} | {1} | {2:.2f} |".format(
                garden.garden_id, garden.n_sessions, garden.mean_gain
            )
        )
    lines.append("")
    lines.append("## Test")
    lines.append("")
    lines.append(
        "Two-sided one-sample t-test of the {0} garden mean gains against a"
        " null gain of {1:.1f} mm/h.".format(n_units, NULL_GAIN)
    )
    lines.append("")
    lines.append("- Mean garden gain: {0:.3f} mm/h".format(mean_gain))
    lines.append("- SD across gardens: {0:.3f} mm/h".format(sd_gain))
    lines.append("- Standard error of the mean: {0:.3f} mm/h".format(se_gain))
    lines.append(
        "- 95% confidence interval: {0:.3f} to {1:.3f} mm/h".format(low, high)
    )
    lines.append("- t({0}) = {1:.3f}, {2}".format(df, float(tstat), p_text))
    lines.append("")
    lines.append(
        "[selected-result] Compost-amended cells infiltrated faster than their"
        " paired reference cells by {0:.3f} mm/h on average (95% CI {1:.3f} to"
        " {2:.3f} mm/h; two-sided one-sample t-test on {3} garden means,"
        " t({4}) = {5:.3f}, {6}).".format(
            mean_gain, low, high, n_units, df, float(tstat), p_text
        )
    )
    lines.append("")
    lines.append("## Reading note")
    lines.append("")
    lines.append(
        "The {0} rows are repeated visits rather than {0} independent gardens."
        " The sample size for the reported test is {1} gardens, which fixes the"
        " degrees of freedom at {2}.".format(n_rows, n_units, df)
    )
    lines.append("")
    return "\n".join(lines)


def main():
    gardens, n_rows = collect_gardens(INPUT_PATH)
    report = build_report(gardens, n_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
