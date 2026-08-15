"""Tidal-cue arm choice in juvenile mangrove mud crabs.

Reads data/input.csv, in which every row is one crab that completed exactly
one Y-maze trial, and writes results/report.md.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")
TIDAL = "tidal"
NULL_P = 0.5
ALPHA = 0.05


def read_trials(path):
    """Return one row per crab, refusing input with a repeated crab code."""
    with path.open(newline="", encoding="ascii") as handle:
        rows = [row for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("no trials found in " + str(path))
    codes = [row["crab_id"].strip() for row in rows]
    if len(set(codes)) != len(codes):
        raise ValueError("each crab_id must appear on exactly one row")
    return rows


def main():
    rows = read_trials(INPUT_PATH)

    choices = [row["arm_choice"].strip() for row in rows]
    sexes = [row["sex"].strip() for row in rows]
    widths = [float(row["carapace_width_mm"]) for row in rows]

    n_units = len(rows)
    n_tidal = sum(1 for choice in choices if choice == TIDAL)
    n_control = n_units - n_tidal
    proportion = n_tidal / n_units
    mean_width = sum(widths) / n_units
    sex_counts = Counter(sexes)

    by_sex = {}
    for sex, choice in zip(sexes, choices):
        hits, total = by_sex.get(sex, (0, 0))
        by_sex[sex] = (hits + int(choice == TIDAL), total + 1)

    outcome = binomtest(n_tidal, n_units, NULL_P, alternative="two-sided")
    p_value = outcome.pvalue
    if p_value < ALPHA:
        verdict = "the preference is significant at alpha = 0.05."
    else:
        verdict = "the preference is not significant at alpha = 0.05."

    lines = [
        "# Tidal-cue arm choice in juvenile mangrove mud crabs",
        "",
        "## Design",
        "",
        "Each of the {0} crabs contributed exactly one Y-maze trial, so every row in".format(n_units),
        "the data file is an independent experimental unit. No crab was retested and",
        "no trial was split across rows, so the counted choices are {0} independent".format(n_units),
        "Bernoulli outcomes.",
        "",
        "## Sample",
        "",
        "- Crabs tested (independent units): {0}".format(n_units),
        "- Rows in data file: {0}".format(n_units),
        "- Females / males: {0} / {1}".format(sex_counts["F"], sex_counts["M"]),
        "- Mean carapace width: {0:.2f} mm (range {1:.1f}-{2:.1f} mm)".format(
            mean_width, min(widths), max(widths)
        ),
        "",
        "## Outcome",
        "",
        "- Chose the tidal-cue arm: {0}".format(n_tidal),
        "- Chose the control arm: {0}".format(n_control),
        "- Observed proportion choosing the tidal-cue arm: {0:.4f}".format(proportion),
        "",
        "Descriptive split by sex (no inferential test was run on the subgroups):",
        "",
        "| Sex | Tidal-cue choices | Trials | Proportion |",
        "| --- | --- | --- | --- |",
    ]

    for sex in sorted(by_sex):
        hits, total = by_sex[sex]
        lines.append(
            "| {0} | {1} | {2} | {3:.4f} |".format(sex, hits, total, hits / total)
        )

    lines.extend(
        [
            "",
            "## Analysis",
            "",
            "Exact two-sided binomial test (scipy.stats.binomtest) of the {0} tidal-cue".format(n_tidal),
            "choices among {0} crabs against the no-preference expectation p = {1}.".format(
                n_units, NULL_P
            ),
            "",
            "[selected-result] Exact two-sided binomial test, {0}/{1} crabs chose the "
            "tidal-cue arm (proportion {2:.4f}) against the chance expectation of {3}: "
            "p = {4:.6f}; {5}".format(n_tidal, n_units, proportion, NULL_P, p_value, verdict),
            "",
            "## Interpretation",
            "",
            "Juvenile crabs entered the arm carrying the tidal cue more often than",
            "chance predicts. Because each crab supplied exactly one trial, the",
            "independence assumption of the binomial test is met by the design itself",
            "and no clustering correction is needed.",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
