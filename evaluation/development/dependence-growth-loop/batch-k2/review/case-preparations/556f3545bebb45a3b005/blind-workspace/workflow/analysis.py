"""Pooled hit-rate test for an archerfish two-choice shooting assay.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
CHANCE_RATE = 0.5
HIT_COLUMN = "chose_target"
UNIT_COLUMN = "fish_tag"


def read_trials(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def tally_by_fish(rows):
    counts = {}
    for row in rows:
        tag = row[UNIT_COLUMN]
        seen, hits = counts.get(tag, (0, 0))
        counts[tag] = (seen + 1, hits + int(row[HIT_COLUMN]))
    return counts


def count_hits(rows):
    return sum(int(row[HIT_COLUMN]) for row in rows)


def build_report(rows, counts, test):
    n = len(rows)
    hits = count_hits(rows)
    rate = hits / n
    lines = [
        "# Archerfish two-choice shooting assay: pooled hit-rate test",
        "",
        "## Data",
        "",
        "Input file: `data/input.csv`",
        f"Rows read: {n}",
        f"Fish tags present: {len(counts)}",
        "",
        "| fish_tag | trials | hits |",
        "| --- | --- | --- |",
    ]
    for tag, (seen, tag_hits) in counts.items():
        lines.append(f"| {tag} | {seen} | {tag_hits} |")
    lines += [
        "",
        "## Analysis",
        "",
        "Each row of the input file is one two-choice shooting trial, scored 1 when the",
        f"fish knocked down the rewarded target and 0 otherwise. All {n} rows were pooled",
        "into a single sequence and entered into an exact two-sided binomial test, one",
        "observation per row, of the null hypothesis that the hit probability of a trial",
        f"equals {CHANCE_RATE:.3f} (scipy.stats.binomtest, alternative \"two-sided\"). No grouping or",
        "weighting of rows was applied before the test.",
        "",
        "## Result",
        "",
        f"Hits: {hits} of {n}",
        f"Observed hit rate: {rate:.3f}",
        f"Exact two-sided binomial p-value: {test.pvalue:.4f}",
        "",
        f"[selected-result] Pooling all {n} trials as independent observations, the fish hit "
        f"the rewarded target in {hits} of {n} trials (hit rate {rate:.3f}); an exact two-sided "
        f"binomial test against a chance rate of {CHANCE_RATE:.3f} gives p = {test.pvalue:.4f}, "
        "so chance performance is rejected at the 0.05 level.",
    ]
    return "\n".join(lines) + "\n"


def main():
    rows = read_trials(INPUT_PATH)
    counts = tally_by_fish(rows)
    test = binomtest(count_hits(rows), len(rows), CHANCE_RATE, alternative="two-sided")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(rows, counts, test), encoding="utf-8")


if __name__ == "__main__":
    main()
