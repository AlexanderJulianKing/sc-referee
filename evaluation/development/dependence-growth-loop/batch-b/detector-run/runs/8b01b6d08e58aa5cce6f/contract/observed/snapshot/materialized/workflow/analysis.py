"""Drone emergence timing in independently reared bumblebee microcolonies.

Reads data/input.csv, where every row is one separately reared microcolony that
was scored a single time, and writes results/report.md.
"""

import csv
import statistics
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COLUMN = "colony_id"
OUTCOME_COLUMN = "days_to_first_drone"
REFERENCE_DAY = 30
NULL_SHARE = 0.5


def read_colonies(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def count_units(records):
    labels = [record[UNIT_COLUMN].strip() for record in records]
    distinct = set(labels)
    if len(distinct) != len(labels):
        raise ValueError(
            "a colony identifier occurs more than once; this design expects "
            "exactly one scored row per colony"
        )
    return len(labels), len(distinct)


def build_report(n_rows, n_units, days, early, late, share, p_value):
    median_days = statistics.median(days)
    mean_days = statistics.fmean(days)
    lines = [
        "# Drone emergence timing in independently reared bumblebee microcolonies",
        "",
        "## Design",
        "",
        f"The {n_rows} commercially sourced *Bombus terrestris* microcolonies in this data set",
        "were reared in separate boxes and scored once each, at the emergence of the",
        f"first drone. Every colony appears in exactly one row ({n_rows} rows, {n_units} distinct",
        "colony identifiers), so the unit of measurement and the unit of analysis",
        "coincide and no colony is counted twice.",
        "",
        "## Analysis",
        "",
        "A colony was classified as early if its first drone emerged before the reference",
        f"day {REFERENCE_DAY} recorded for this stock. The share of early colonies was compared with the",
        f"no-shift expectation of {NULL_SHARE} using an exact two-sided binomial test on the {n_rows}",
        "independent colony-level outcomes.",
        "",
        "## Results",
        "",
        f"- Colonies analysed: {n_rows} (distinct colony identifiers: {n_units})",
        f"- Days to first drone: median {median_days:.1f}, mean {mean_days:.2f}, range {min(days)} to {max(days)}",
        f"- Early colonies (fewer than {REFERENCE_DAY} days): {early} of {n_rows}, share {share:.3f}",
        f"- Colonies at or past day {REFERENCE_DAY}: {late} of {n_rows}",
        f"- Exact two-sided binomial test against a share of {NULL_SHARE}: p = {p_value:.4f}",
        "",
        (
            f"[selected-result] Drones emerged before reference day {REFERENCE_DAY} in {early} of "
            f"{n_rows} independently reared colonies (share {share:.3f}), which is more often than "
            f"the no-shift expectation of {NULL_SHARE} (exact two-sided binomial test, "
            f"p = {p_value:.4f})."
        ),
        "",
        "## Reading the result",
        "",
        "The test consumes one number per colony, and each colony was reared and scored",
        f"on its own, so the {n_rows} observations are the {n_units} independent units and no",
        "within-colony replication enters the count. The result speaks only to how often",
        "early emergence occurred, not to the size of the shift in days.",
    ]
    return "\n".join(lines) + "\n"


def main():
    records = read_colonies(INPUT_PATH)
    n_rows, n_units = count_units(records)

    days = [int(record[OUTCOME_COLUMN]) for record in records]
    early = sum(1 for value in days if value < REFERENCE_DAY)
    late = n_rows - early
    share = early / n_rows

    test = binomtest(early, n_rows, NULL_SHARE, alternative="two-sided")

    report = build_report(n_rows, n_units, days, early, late, share, test.pvalue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
