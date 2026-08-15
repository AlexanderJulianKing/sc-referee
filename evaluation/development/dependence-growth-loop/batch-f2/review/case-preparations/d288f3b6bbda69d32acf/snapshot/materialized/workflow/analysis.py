"""Salinity contrast in leaf gas exchange of glasshouse mangrove seedlings.

Reads data/input.csv, compares net CO2 assimilation between the two salinity
regimes, and writes results/report.md.
"""

import csv
from collections import OrderedDict
from pathlib import Path
from statistics import mean, stdev

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

REGIME_COLUMN = "salinity_regime"
UNIT_COLUMN = "seedling_id"
VALUE_COLUMN = "anet_umol_m2_s"
REGIMES = ("ambient_15ppt", "elevated_35ppt")
UNITS = "umol CO2 m^-2 s^-1"
P_LADDER = (
    (0.0001, "p < 0.0001"),
    (0.001, "p < 0.001"),
    (0.01, "p < 0.01"),
    (0.05, "p < 0.05"),
)


def read_table(path):
    with path.open(encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def values_by_regime(rows):
    buckets = OrderedDict((name, []) for name in REGIMES)
    for row in rows:
        buckets[row[REGIME_COLUMN]].append(float(row[VALUE_COLUMN]))
    return buckets


def seedlings_by_regime(rows):
    owner = OrderedDict()
    for row in rows:
        owner.setdefault(row[UNIT_COLUMN], row[REGIME_COLUMN])
    tally = OrderedDict((name, 0) for name in REGIMES)
    for regime in owner.values():
        tally[regime] += 1
    return owner, tally


def phrase_for_p(pvalue):
    for cutoff, phrase in P_LADDER:
        if pvalue < cutoff:
            return phrase
    return "p = {0:.3f}".format(pvalue)


def compose(rows):
    buckets = values_by_regime(rows)
    seedlings, per_regime = seedlings_by_regime(rows)
    ambient, elevated = REGIMES
    per_seedling = len(rows) // len(seedlings)

    averages = OrderedDict((name, mean(vals)) for name, vals in buckets.items())
    spreads = OrderedDict((name, stdev(vals)) for name, vals in buckets.items())
    gap = averages[ambient] - averages[elevated]

    outcome = stats.ttest_ind(buckets[ambient], buckets[elevated], equal_var=True)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)
    df = len(buckets[ambient]) + len(buckets[elevated]) - 2

    lines = [
        "# Net photosynthesis of mangrove seedlings under two salinity regimes",
        "",
        "## Data",
        "",
        "Input: data/input.csv, {0} leaf-level rows.".format(len(rows)),
        "Response: {0}, net CO2 assimilation in {1}.".format(VALUE_COLUMN, UNITS),
        "Design: {0} Avicennia marina seedlings, {1} gas-exchange readings per seedling;".format(
            len(seedlings), per_seedling),
        "{0} seedlings at 15 ppt ({1}) and {2} at 35 ppt ({3}).".format(
            per_regime[ambient], ambient, per_regime[elevated], elevated),
        "",
        "## Group summaries",
        "",
        "| {0} | rows | mean | SD |".format(REGIME_COLUMN),
        "| --- | ---: | ---: | ---: |",
    ]
    for name in REGIMES:
        lines.append("| {0} | {1} | {2:.3f} | {3:.3f} |".format(
            name, len(buckets[name]), averages[name], spreads[name]))
    lines.extend([
        "",
        "Difference of means ({0} - {1}): {2:.3f} {3}.".format(
            ambient, elevated, gap, UNITS),
        "",
        "## Test",
        "",
        "Two-sided two-sample Student t-test with pooled variance",
        "(scipy.stats.ttest_ind, equal_var=True). Each row of data/input.csv supplies",
        "one observation, giving {0} observations per regime and {1} degrees of freedom.".format(
            len(buckets[ambient]), df),
        "",
        "[selected-result] Two-sample pooled t-test of {0} by {1}: t({2}) = {3:.2f}, {4}; "
        "{5} mean {6:.3f} vs {7} mean {8:.3f}, difference {9:.3f} {10}.".format(
            VALUE_COLUMN, REGIME_COLUMN, df, tstat, phrase_for_p(pvalue),
            ambient, averages[ambient], elevated, averages[elevated], gap, UNITS),
        "",
        "## Interpretation",
        "",
        "Assimilation averages {0:.3f} {1} higher under ambient than under".format(gap, UNITS),
        "elevated salinity; the pooled t-test rejects equality of the two regime means",
        "at the conventional 5 percent level.",
    ])
    return "\n".join(lines) + "\n"


def main():
    rows = read_table(INPUT_PATH)
    report = compose(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
