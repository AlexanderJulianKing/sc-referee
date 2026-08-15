"""Spring colony strength after overwintering with or without a hive wrap.

Each colony is weighed exactly once, so one row is one independent unit and
a row-level rank test is the appropriate instrument.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COLUMN = "hive_id"
GROUP_COLUMN = "wrap_treatment"
RESPONSE_COLUMN = "spring_cluster_mass_kg"


def read_records(path):
    with path.open(newline="", encoding="ascii") as handle:
        records = list(csv.DictReader(handle))
    if not records:
        raise ValueError("no colony rows in " + str(path))
    return records


def check_one_row_per_colony(records):
    tally = {}
    for record in records:
        colony = record[UNIT_COLUMN]
        tally[colony] = tally.get(colony, 0) + 1
    duplicated = sorted(name for name, count in tally.items() if count > 1)
    if duplicated:
        raise ValueError("more than one row for: " + ", ".join(duplicated))


def collect_masses(records):
    masses = {}
    for record in records:
        masses.setdefault(record[GROUP_COLUMN], []).append(
            float(record[RESPONSE_COLUMN]))
    if len(masses) != 2:
        raise ValueError("expected exactly two wrap treatments")
    return masses


def build_report(records, masses, outcome):
    labels = sorted(masses)
    bare_label, wrap_label = labels
    bare = masses[bare_label]
    wrapped = masses[wrap_label]
    pairs = len(bare) * len(wrapped)
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    share = (pairs - u_stat) / pairs
    gap = statistics.fmean(wrapped) - statistics.fmean(bare)

    lines = [
        "# Overwinter wrapping and spring cluster mass in honey bee colonies",
        "",
        "## Design",
        "",
        "{0} overwintered colonies were weighed once each at the first spring".format(
            len(records)),
        "inspection. Every colony ({0}) appears in exactly one row, so the".format(
            UNIT_COLUMN),
        "analysed values are {0} independent units with no repeated measurements.".format(
            len(records)),
        "",
        "| {0} | colonies | mean mass (kg) | median mass (kg) |".format(GROUP_COLUMN),
        "| --- | --- | --- | --- |",
    ]
    for label in labels:
        values = masses[label]
        lines.append("| {0} | {1} | {2:.2f} | {3:.2f} |".format(
            label, len(values), statistics.fmean(values),
            statistics.median(values)))
    lines.extend([
        "",
        "## Test",
        "",
        "Two-sided Mann-Whitney U test on spring cluster mass, exact null",
        "distribution, {0} {1} colonies versus {2} {3} colonies (one value per".format(
            len(bare), bare_label, len(wrapped), wrap_label),
        "colony).",
        "",
        "- U = {0:.1f}, computed with the {1} colonies as the first sample".format(
            u_stat, bare_label),
        "- p = {0:.6f}".format(p_value),
        "- {0} colony heavier in {1:.3f} of the {2} cross-treatment pairs".format(
            wrap_label, share, pairs),
        "- mean difference ({0} minus {1}) = {2:.2f} kg".format(
            wrap_label, bare_label, gap),
        "",
        "## Interpretation",
        "",
        "Spring cluster mass was higher in {0} colonies than in {1} colonies.".format(
            wrap_label, bare_label),
        "Because each colony supplies a single value, the rank test's independence",
        "assumption is met by the design and the p-value needs no clustering",
        "correction. With {0} colonies per arm the size of the gap is still".format(
            len(wrapped)),
        "estimated coarsely.",
        "",
        "[selected-result] {0} colonies had higher spring cluster mass than {1}"
        " colonies: exact two-sided Mann-Whitney U = {2:.1f} with {3} versus {4}"
        " independent colonies, p = {5:.6f} (mean difference {6:.2f} kg).".format(
            wrap_label.capitalize(), bare_label, u_stat, len(bare),
            len(wrapped), p_value, gap),
    ])
    return "\n".join(lines) + "\n"


def main():
    records = read_records(INPUT_PATH)
    check_one_row_per_colony(records)
    masses = collect_masses(records)
    bare_label, wrap_label = sorted(masses)
    outcome = stats.mannwhitneyu(masses[bare_label], masses[wrap_label],
                                 alternative="two-sided", method="exact")
    report = build_report(records, masses, outcome)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()
