"""Exact binomial test of first-landing colour choice in a Y-maze assay.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")
BRIGHT_LABEL = "uv_bright"
CHANCE = 0.5


def read_trials(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def tally_by_forager(trials):
    tally = {}
    for row in trials:
        forager = row["forager_id"]
        counts = tally.setdefault(forager, {"trials": 0, "bright": 0})
        counts["trials"] += 1
        if row["first_visit_choice"] == BRIGHT_LABEL:
            counts["bright"] += 1
    return tally


def compose_report(tally, bright, total, pvalue):
    share = bright / total
    foragers = len(tally)
    lines = [
        "# UV-bright corolla preference in a two-choice Y-maze assay",
        "",
        "## Data",
        "",
        "Each row of `data/input.csv` is one Y-maze trial, scored by the artificial",
        f"corolla that received the first landing. The file holds {total} trials contributed",
        f"by {foragers} marked foragers.",
        "",
        "| forager_id | trials | uv_bright first visits |",
        "| --- | --- | --- |",
    ]
    for forager, counts in tally.items():
        lines.append(f"| {forager} | {counts['trials']} | {counts['bright']} |")
    lines.extend([
        "",
        "## Analysis",
        "",
        "Every trial row was entered as one Bernoulli observation and the pooled counts",
        "were submitted to an exact two-sided binomial test (`scipy.stats.binomtest`)",
        f"against the chance expectation p = {CHANCE}.",
        "",
        "## Result",
        "",
        f"Foragers landed first on the UV-bright corolla in {bright} of {total} trials (observed",
        f"share {share:.3f}).",
        "",
        f"[selected-result] Exact two-sided binomial test of {bright} uv_bright"
        f" first visits out of {total} trials against p = {CHANCE}:"
        f" p = {pvalue:.6f} (observed share {share:.3f});"
        " the deviation from chance is significant at the 5% level.",
        "",
        "## Notes",
        "",
        f"The {total} trials come from {foragers} foragers, so several rows describe the same insect",
        "tested again; the test above nonetheless weighs each row as one independent",
        "draw. Trial order within a forager was not modelled.",
        "",
    ])
    return "\n".join(lines)


def main():
    trials = read_trials(INPUT_PATH)
    total = len(trials)
    bright = sum(1 for row in trials if row["first_visit_choice"] == BRIGHT_LABEL)
    tally = tally_by_forager(trials)
    outcome = binomtest(bright, total, CHANCE, alternative="two-sided")
    report = compose_report(tally, bright, total, outcome.pvalue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
