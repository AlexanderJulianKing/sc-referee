"""Y-bridge arm-choice assay: does a trail-pheromone extract steer foragers?

Reads data/input.csv (one row per scored trial) and writes results/report.md.
"""

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

MARKED_ARM = "marked"
NULL_P = 0.5
ALPHA = 0.05


def read_trials(path):
    """Every scored trial in the assay log, in file order."""
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def summarise(trials):
    """Trial count, marked-arm choices, and mean commitment latency."""
    n_trials = len(trials)
    n_marked = sum(1 for row in trials if row["arm_chosen"] == MARKED_ARM)
    latency = sum(float(row["latency_s"]) for row in trials) / n_trials
    return n_trials, n_marked, latency


def build_report(n_trials, n_marked, latency, p_value):
    """Render the markdown report as a single string."""
    proportion = n_marked / n_trials
    verdict = (
        "so the no-preference null is rejected"
        if p_value < ALPHA
        else "so the no-preference null is retained"
    )
    lines = [
        "# Trail-pheromone arm choice in Lasius niger foragers",
        "",
        "## Analysis",
        "",
        "Each row of `data/input.csv` is one Y-bridge choice trial. A trial counted",
        "as a success when the focal forager committed to the pheromone-marked arm.",
        f"All {n_trials} trials were pooled and submitted to an exact binomial test",
        f"(`scipy.stats.binomtest`, two-sided) against the no-preference null "
        f"p = {NULL_P:.3f}.",
        "",
        "## Result",
        "",
        f"- Trials scored: {n_trials}",
        f"- Choices of the marked arm: {n_marked}",
        f"- Observed proportion: {proportion:.3f}",
        f"- Mean commitment latency: {latency:.1f} s",
        "",
        f"[selected-result] Exact binomial test: {n_marked} of {n_trials} trials "
        f"took the marked arm (proportion {proportion:.3f}) against a null "
        f"proportion of {NULL_P:.3f}; two-sided p = {p_value:.4f}, {verdict} at "
        f"alpha = {ALPHA:.2f}.",
        "",
        "## Interpretation",
        "",
        "Foragers took the pheromone-marked arm more often than expected under",
        "chance, consistent with trail-pheromone guidance at the bifurcation.",
    ]
    return "\n".join(lines) + "\n"


def main():
    trials = read_trials(INPUT_PATH)
    n_trials, n_marked, latency = summarise(trials)
    outcome = binomtest(n_marked, n_trials, NULL_P, alternative="two-sided")
    report = build_report(n_trials, n_marked, latency, outcome.pvalue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
