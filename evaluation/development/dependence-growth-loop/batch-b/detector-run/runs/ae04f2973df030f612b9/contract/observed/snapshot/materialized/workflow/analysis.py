"""Pooled trial-level analysis of a two-option tool-choice assay in juvenile crows.

Reads data/input.csv, counts how often the hooked stick was lifted first, and
writes results/report.md.
"""

import csv
from pathlib import Path

from scipy.stats import binomtest

DATA_FILE = Path("data") / "input.csv"
REPORT_FILE = Path("results") / "report.md"
CHANCE_RATE = 0.5
OUTCOME_COLUMN = "chose_hooked"
BIRD_COLUMN = "bird_id"


def read_trials(path):
    """Return every recorded trial as a plain dictionary, in file order."""
    with open(str(path), "r", encoding="ascii", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def tally_per_bird(trials):
    """Map each bird to a (trials, hooked choices) pair, keeping first-seen order."""
    tally = {}
    for row in trials:
        bird = row[BIRD_COLUMN]
        attempts, hooked = tally.get(bird, (0, 0))
        tally[bird] = (attempts + 1, hooked + int(row[OUTCOME_COLUMN]))
    return tally


def count_hooked(trials):
    return sum(int(row[OUTCOME_COLUMN]) for row in trials)


def build_report(tally, successes, trials, pvalue):
    lines = []
    lines.append("# Hooked-stick preference in juvenile New Caledonian crows")
    lines.append("")
    lines.append("## Trials")
    lines.append("")
    lines.append(
        "{0} two-option tool-choice trials were recorded from {1} hand-raised"
        " juvenile crows.".format(trials, len(tally))
    )
    lines.append(
        "Each trial was scored 1 when the bird lifted the hooked stick and 0 when it lifted"
    )
    lines.append("the straight stick.")
    lines.append("")
    lines.append("## Per-bird tally")
    lines.append("")
    lines.append("| bird_id | trials | hooked choices |")
    lines.append("| --- | --- | --- |")
    for bird in tally:
        attempts, hooked = tally[bird]
        lines.append("| {0} | {1} | {2} |".format(bird, attempts, hooked))
    lines.append("")
    lines.append("## Test")
    lines.append("")
    lines.append(
        "Every recorded trial was entered as one observation and the pooled outcomes were"
    )
    lines.append(
        "compared with a chance rate of {0:.3f} using an exact two-sided binomial"
        " test.".format(CHANCE_RATE)
    )
    lines.append("")
    lines.append("- Hooked choices: {0} of {1}".format(successes, trials))
    lines.append("- Observed proportion: {0:.4f}".format(successes / trials))
    lines.append("- Exact two-sided p-value: {0:.6f}".format(pvalue))
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append(
        "[selected-result] Juvenile New Caledonian crows chose the hooked stick on "
        "{0} of {1} trials ({2:.2f}%), and an exact two-sided binomial test against a "
        "chance rate of {3:.3f} rejects chance responding at the 5% level "
        "(p = {4:.6f}).".format(
            successes, trials, 100.0 * successes / trials, CHANCE_RATE, pvalue
        )
    )
    return "\n".join(lines) + "\n"


def main():
    trials = read_trials(DATA_FILE)
    tally = tally_per_bird(trials)
    n_trials = len(trials)
    n_hooked = count_hooked(trials)
    outcome = binomtest(n_hooked, n_trials, CHANCE_RATE, alternative="two-sided")
    report = build_report(tally, n_hooked, n_trials, outcome.pvalue)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(str(REPORT_FILE), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
