"""Littoral shelf restoration and great crested newt eDNA in quarry ponds.

Reads data/input.csv (one abandoned quarry pond per row, one survey per pond)
and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

SHELF_LEVELS = ("restored", "unrestored")
POSITIVE = "detected"
NEGATIVE = "not_detected"


def read_surveys(path):
    with path.open(newline="", encoding="ascii") as handle:
        surveys = list(csv.DictReader(handle))
    if not surveys:
        raise ValueError("data/input.csv contains no survey rows")
    return surveys


def check_one_survey_per_pond(surveys):
    pond_ids = [row["pond_id"] for row in surveys]
    if len(set(pond_ids)) != len(pond_ids):
        raise ValueError("pond_id values repeat; the design is one survey per pond")


def cross_tabulate(surveys):
    counts = {level: {POSITIVE: 0, NEGATIVE: 0} for level in SHELF_LEVELS}
    for row in surveys:
        shelf = row["shelf_status"]
        outcome = row["edna_result"]
        if shelf not in counts:
            raise ValueError("unrecognised shelf_status: " + shelf)
        if outcome not in (POSITIVE, NEGATIVE):
            raise ValueError("unrecognised edna_result: " + outcome)
        counts[shelf][outcome] += 1
    return counts


def compose(counts, odds_ratio, p_value):
    hits = {lv: counts[lv][POSITIVE] for lv in SHELF_LEVELS}
    misses = {lv: counts[lv][NEGATIVE] for lv in SHELF_LEVELS}
    sizes = {lv: hits[lv] + misses[lv] for lv in SHELF_LEVELS}
    rates = {lv: hits[lv] / sizes[lv] for lv in SHELF_LEVELS}
    total = sizes["restored"] + sizes["unrestored"]
    gap = rates["restored"] - rates["unrestored"]

    lines = [
        "# Littoral shelf restoration and great crested newt eDNA detection",
        "",
        "## Design",
        "",
        "Each row of `data/input.csv` is one abandoned quarry pond. Every pond was",
        "visited once and contributed exactly one pooled water sample, screened for",
        "great crested newt eDNA. Pond identifiers are unique, so the "
        + str(total)
        + " ponds",
        "supply "
        + str(total)
        + " mutually independent observations with no repeated measures.",
        "",
        "## Analysis",
        "",
        "Two-sided Fisher exact test on the 2 x 2 table of shelf status by eDNA result.",
        "",
        "| Shelf status | Detected | Not detected | Ponds | Detection rate |",
        "| --- | --- | --- | --- | --- |",
    ]

    for lv in SHELF_LEVELS:
        lines.append(
            "| {0} | {1} | {2} | {3} | {4:.3f} |".format(
                lv, hits[lv], misses[lv], sizes[lv], rates[lv]
            )
        )

    lines += [
        "",
        "## Result",
        "",
        "- Sample odds ratio: {0:.2f}".format(odds_ratio),
        "- Two-sided exact p-value: {0:.4f}".format(p_value),
        "- Detection-rate difference (restored minus unrestored): {0:.3f}".format(gap),
        "",
        "[selected-result] A two-sided Fisher exact test on {0} independently".format(
            total
        )
        + " surveyed quarry ponds returns p = {0:.4f} with a sample odds ratio".format(
            p_value
        )
        + " of {0:.2f}; great crested newt eDNA was detected in {1} of {2}".format(
            odds_ratio, hits["restored"], sizes["restored"]
        )
        + " restored-shelf ponds ({0:.3f}) against {1} of {2} unrestored ponds".format(
            rates["restored"], hits["unrestored"], sizes["unrestored"]
        )
        + " ({0:.3f}).".format(rates["unrestored"]),
        "",
        "## Reading note",
        "",
        "Fisher's exact test treats each row as an independent trial. That assumption",
        "matches the sampling frame used here, which allocates one and only one survey",
        "to each pond, so no pond is counted more than once.",
    ]

    return "\n".join(lines) + "\n"


def main():
    surveys = read_surveys(INPUT_PATH)
    check_one_survey_per_pond(surveys)
    counts = cross_tabulate(surveys)
    table = [[counts[lv][POSITIVE], counts[lv][NEGATIVE]] for lv in SHELF_LEVELS]
    odds_ratio, p_value = fisher_exact(table)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(compose(counts, odds_ratio, p_value))


if __name__ == "__main__":
    main()
