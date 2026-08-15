"""Deficit-irrigation crossover in potted olive saplings.

Reads the long-format midday session log in data/input.csv, collapses the repeated
sessions of each sapling into one mean per irrigation schedule, and writes the
sapling-level paired comparison to results/report.md.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

DEFICIT = "deficit"
FULL = "full"
CONDUCTANCE_COLUMN = "stomatal_conductance_mmol_m2_s"


def average(values):
    return sum(values) / len(values)


def read_sessions(path):
    """Return ({sapling_id: {regime: [conductance, ...]}}, number of session rows)."""
    by_sapling = defaultdict(lambda: defaultdict(list))
    session_rows = 0
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            sapling = row["sapling_id"].strip()
            regime = row["irrigation_regime"].strip()
            by_sapling[sapling][regime].append(float(row[CONDUCTANCE_COLUMN]))
            session_rows += 1
    if not by_sapling:
        raise ValueError("no session rows found in " + path.as_posix())
    return by_sapling, session_rows


def collapse_to_saplings(by_sapling):
    """Reduce repeated sessions to one deficit mean and one full mean per sapling."""
    sapling_ids = sorted(by_sapling)
    deficit_means = []
    full_means = []
    for sapling in sapling_ids:
        regimes = by_sapling[sapling]
        if sorted(regimes) != [DEFICIT, FULL]:
            raise ValueError("sapling " + sapling + " is missing an irrigation schedule")
        deficit_means.append(average(regimes[DEFICIT]))
        full_means.append(average(regimes[FULL]))
    return sapling_ids, deficit_means, full_means


def build_report(session_rows, sapling_ids, deficit_means, full_means):
    n = len(sapling_ids)
    sessions_per_sapling = session_rows // n
    diffs = [d - f for d, f in zip(deficit_means, full_means)]
    mean_diff = average(diffs)
    sd_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / (n - 1))
    se_diff = sd_diff / math.sqrt(n)
    df = n - 1

    test = stats.ttest_rel(deficit_means, full_means)
    half_width = stats.t.ppf(0.975, df) * se_diff
    lo = mean_diff - half_width
    hi = mean_diff + half_width
    if test.pvalue < 0.001:
        p_text = "p < 0.001"
    else:
        p_text = "p = {0:.3f}".format(test.pvalue)

    selected = (
        "[selected-result] Midday stomatal conductance was {0:.2f} mmol m^-2 s^-1 lower"
        " on the deficit schedule than on the full schedule (95% CI [{1:.2f}, {2:.2f}];"
        " two-sided paired t-test on {3} sapling-level means, t({4}) = {5:.2f}, {6})."
    ).format(abs(mean_diff), lo, hi, n, df, test.statistic, p_text)

    lines = [
        "# Midday stomatal conductance under deficit irrigation in potted olive saplings",
        "",
        "## Data",
        "",
        "Source: {0}, {1} midday gas-exchange sessions recorded in".format(
            INPUT_PATH.as_posix(), session_rows
        ),
        "long format. The {0} potted olive saplings were each measured on {1} dates: two sessions".format(
            n, sessions_per_sapling
        ),
        "on the deficit schedule and two on the full schedule, in a counterbalanced crossover",
        "order.",
        "",
        "## Analysis",
        "",
        "Sessions repeated on the same sapling are not independent observations, so the {0}".format(
            sessions_per_sapling
        ),
        "sessions belonging to a sapling were first collapsed into one deficit mean and one",
        "full mean for that sapling. The reported comparison is a two-sided paired t-test on",
        "the {0} sapling-level regime means, giving exactly one analysed row per sapling.".format(n),
        "",
        "## Result",
        "",
        "- Sapling-level mean conductance, deficit schedule: {0:.2f} mmol m^-2 s^-1".format(
            average(deficit_means)
        ),
        "- Sapling-level mean conductance, full schedule: {0:.2f} mmol m^-2 s^-1".format(
            average(full_means)
        ),
        "- Mean within-sapling difference (deficit minus full): {0:.2f} mmol m^-2 s^-1 (SD {1:.2f})".format(
            mean_diff, sd_diff
        ),
        "- 95% CI for the mean difference: [{0:.2f}, {1:.2f}]".format(lo, hi),
        "- Paired t-test: t({0}) = {1:.2f}, {2}".format(df, test.statistic, p_text),
        "",
        selected,
    ]
    return "\n".join(lines) + "\n"


def main():
    by_sapling, session_rows = read_sessions(INPUT_PATH)
    sapling_ids, deficit_means, full_means = collapse_to_saplings(by_sapling)
    report = build_report(session_rows, sapling_ids, deficit_means, full_means)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
