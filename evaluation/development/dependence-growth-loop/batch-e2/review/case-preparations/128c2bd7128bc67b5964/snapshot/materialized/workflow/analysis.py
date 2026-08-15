"""Pooled arm-choice analysis for the darkened T-junction assay."""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")
RIGHT_ARM = "right"
NULL_RATE = 0.5


def read_trials():
    with INPUT_PATH.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def tally_by_animal(trials):
    tallies = {}
    for trial in trials:
        total, rights = tallies.get(trial["animal_id"], (0, 0))
        scored = 1 if trial["arm_chosen"] == RIGHT_ARM else 0
        tallies[trial["animal_id"]] = (total + 1, rights + scored)
    return dict(sorted(tallies.items()))


def compose(trials):
    n_trials = len(trials)
    n_right = sum(1 for trial in trials if trial["arm_chosen"] == RIGHT_ARM)
    pooled_share = n_right / n_trials
    mean_latency = sum(float(trial["latency_s"]) for trial in trials) / n_trials
    p_value = binomtest(n_right, n_trials, NULL_RATE, alternative="two-sided").pvalue

    tallies = tally_by_animal(trials)
    n_animals = len(tallies)
    runs_each = n_trials // n_animals
    shares = [rights / total for total, rights in tallies.values()]

    out = [
        "# Right-arm bias at a darkened T-junction",
        "",
        "## Data",
        "",
        f"The file `data/input.csv` records {n_trials} T-junction trials from {n_animals} whip spiders,",
        f"{runs_each} trials per animal. Each row is one trial and stores the arm the animal",
        "entered and its latency to the choice point in seconds.",
        "",
        "## Analysis",
        "",
        "Every trial in the file was treated as one Bernoulli observation. The pooled",
        f"count of right-arm entries was compared against a chance rate of {NULL_RATE} with an",
        "exact two-sided binomial test (scipy.stats.binomtest).",
        "",
        "## Per-animal tallies",
        "",
        "| animal_id | trials | right-arm entries | share |",
        "| --- | --- | --- | --- |",
    ]
    for animal, (total, rights) in tallies.items():
        out.append(f"| {animal} | {total} | {rights} | {rights / total:.3f} |")
    out += [
        "",
        "## Result",
        "",
        f"Right-arm entries: {n_right} of {n_trials} trials (pooled share {pooled_share:.3f}).",
        f"Exact two-sided binomial test against {NULL_RATE}: p = {p_value:.4f}.",
        f"Mean latency to the choice point: {mean_latency:.1f} s.",
        "",
        f"[selected-result] Exact two-sided binomial test on {n_trials} pooled trials with "
        f"{n_right} right-arm entries against a chance rate of {NULL_RATE} gives "
        f"p = {p_value:.4f} (pooled share {pooled_share:.3f}), a departure from chance at "
        "the 0.05 level.",
        "",
        "## Notes",
        "",
        f"The {n_trials} trials come from {n_animals} animals, {runs_each} trials each, and the",
        f"per-animal shares span {min(shares):.3f} to {max(shares):.3f}. Each trial contributes",
        "one observation to the test above.",
    ]
    return "\n".join(out) + "\n"


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(compose(read_trials()), encoding="utf-8")


if __name__ == "__main__":
    main()
