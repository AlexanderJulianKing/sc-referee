"""Does a floating duckweed canopy help founder Daphnia populations persist?

Each outdoor mesocosm pond was assigned to one canopy treatment and scored
once at the end of the season, so every pond supplies exactly one row of
data/input.csv and exactly one trial for the exact test performed here.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

CANOPY_LEVELS = ("shaded", "open")
OUTCOME_LEVELS = ("persisted", "collapsed")


def read_ponds():
    with INPUT_PATH.open(newline="", encoding="ascii") as handle:
        ponds = [dict(record) for record in csv.DictReader(handle)]
    labels = [pond["pond_id"] for pond in ponds]
    if len(set(labels)) != len(labels):
        raise ValueError("pond_id must be unique: one pond, one row, one trial")
    for pond in ponds:
        if pond["canopy"] not in CANOPY_LEVELS:
            raise ValueError("unexpected canopy level: " + pond["canopy"])
        if pond["outcome"] not in OUTCOME_LEVELS:
            raise ValueError("unexpected outcome level: " + pond["outcome"])
    return ponds


def contingency(ponds):
    tally = Counter((pond["canopy"], pond["outcome"]) for pond in ponds)
    return [
        [tally[(canopy, outcome)] for outcome in OUTCOME_LEVELS]
        for canopy in CANOPY_LEVELS
    ]


def sample_odds_ratio(table):
    (yes_a, no_a), (yes_b, no_b) = table
    if no_a == 0 or yes_b == 0:
        return float("inf")
    return (yes_a * no_b) / (no_a * yes_b)


def compose(ponds, table, odds_ratio, p_value):
    (shaded_yes, shaded_no), (open_yes, open_no) = table
    shaded_n = shaded_yes + shaded_no
    open_n = open_yes + open_no
    shaded_rate = shaded_yes / shaded_n
    open_rate = open_yes / open_n
    n_ponds = len(ponds)
    lines = [
        "# Canopy shading and Daphnia persistence in outdoor mesocosms",
        "",
        "## Design",
        "",
        f"Each of the {n_ponds} outdoor mesocosm ponds was stocked once with a founder",
        "Daphnia pulex population, assigned to one canopy treatment, and scored once",
        "at the end of the season as either persisted or collapsed. The pond is both",
        "the unit of assignment and the unit of analysis: every pond_id value appears",
        "in exactly one row, so no pond contributes more than a single outcome to the",
        "table below.",
        "",
        "## Counts",
        "",
        "| canopy | persisted | collapsed | ponds | persistence rate |",
        "| --- | --- | --- | --- | --- |",
        f"| shaded | {shaded_yes} | {shaded_no} | {shaded_n} | {shaded_rate * 100:.1f}% |",
        f"| open | {open_yes} | {open_no} | {open_n} | {open_rate * 100:.1f}% |",
        "",
        "## Test",
        "",
        "Two-sided Fisher exact test on the 2x2 table of independent ponds, one trial",
        "per pond.",
        "",
        f"- sample odds ratio: {odds_ratio:.3f}",
        f"- two-sided p-value: {p_value:.6f}",
        f"- difference in persistence rate (shaded - open): {shaded_rate - open_rate:.3f}",
        "",
        f"[selected-result] Two-sided Fisher exact test on {n_ponds} independent mesocosm"
        f" ponds: shaded ponds persisted in {shaded_yes} of {shaded_n} cases versus"
        f" {open_yes} of {open_n} open ponds (sample odds ratio {odds_ratio:.3f},"
        f" p = {p_value:.6f}), so canopy shading is associated with higher persistence"
        " at the 5% level.",
        "",
        "## Reading the result",
        "",
        "The exact p-value is the sum of hypergeometric probabilities no larger than",
        "that of the observed table under fixed row and column margins. Each pond",
        "enters the table once, so the fixed margins refer to independent ponds and no",
        "within-pond replication inflates the counts. Volume, stocking density and",
        "mean surface temperature were recorded but not used as strata, so the",
        f"association is unadjusted, and with {n_ponds} ponds in total the odds ratio is",
        "imprecise.",
    ]
    return "\n".join(lines) + "\n"


def main():
    ponds = read_ponds()
    table = contingency(ponds)
    _, p_value = fisher_exact(table, alternative="two-sided")
    odds_ratio = sample_odds_ratio(table)
    report = compose(ponds, table, odds_ratio, p_value)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
