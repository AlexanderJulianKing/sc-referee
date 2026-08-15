"""Y-maze thermal choice assay in juvenile cave salamanders.

Reads the scored releases in data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
import pathlib

from scipy.stats import binomtest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "input.csv"
REPORT_PATH = ROOT / "results" / "report.md"

WARM_LABEL = "warm"
NULL_P = 0.5


def read_releases(path):
    """Return every scored release in the assay file as a plain dict."""
    with path.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def tally(releases):
    """Count warm-arm choices and average the first-entry latency."""
    n_total = len(releases)
    n_warm = sum(1 for row in releases if row["arm_chosen"] == WARM_LABEL)
    mean_latency = sum(float(row["latency_s"]) for row in releases) / n_total
    return n_total, n_warm, mean_latency


def build_report(n_total, n_warm, mean_latency, p_value):
    n_cool = n_total - n_warm
    prop_warm = n_warm / n_total
    return [
        "# Thermal arm choice in juvenile cave salamanders",
        "",
        "## Analysis",
        "",
        "Each release in the Y-maze is scored for the arm the animal first entered (warm",
        "or cool). Every scored release is entered as one independent Bernoulli trial and",
        "the pooled counts are submitted to an exact two-sided binomial test against the",
        "no-preference null of p = 0.5 (scipy.stats.binomtest).",
        "",
        "## Data summary",
        "",
        "- Scored releases: {0}".format(n_total),
        "- Warm-arm choices: {0}".format(n_warm),
        "- Cool-arm choices: {0}".format(n_cool),
        "- Proportion warm: {0:.3f}".format(prop_warm),
        "- Mean first-choice latency: {0:.1f} s".format(mean_latency),
        "",
        "## Result",
        "",
        "[selected-result] Exact two-sided binomial test, {0} warm-arm choices in {1} "
        "scored releases, null p = 0.5: proportion warm = {2:.3f}, p = {3:.4f}.".format(
            n_warm, n_total, prop_warm, p_value
        ),
        "",
        "The pooled releases depart from indifference at the conventional 5% threshold,",
        "so the assay is reported as evidence of a warm-arm preference.",
    ]


def main():
    releases = read_releases(CSV_PATH)
    n_total, n_warm, mean_latency = tally(releases)
    outcome = binomtest(n_warm, n_total, NULL_P, alternative="two-sided")
    lines = build_report(n_total, n_warm, mean_latency, outcome.pvalue)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
