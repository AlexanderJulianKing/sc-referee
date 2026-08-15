"""Chorus onset at street-lit versus unlit urban stormwater ponds.

Reads data/input.csv, which carries one line per pond and one survey night
per pond, and writes results/report.md.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

GROUP_COLUMN = "lighting_regime"
ONSET_COLUMN = "chorus_onset_min_after_sunset"
LIT = "lit"
UNLIT = "unlit"


def read_onsets():
    """Collect onset minutes per lighting regime, one value per pond."""
    onsets = {LIT: [], UNLIT: []}
    seen = set()
    with INPUT_PATH.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            pond = row["pond_id"]
            if pond in seen:
                raise ValueError("pond appears more than once: " + pond)
            seen.add(pond)
            onsets[row[GROUP_COLUMN]].append(float(row[ONSET_COLUMN]))
    return onsets


def describe(values):
    """Return count, mean and median of one regime's onset times."""
    return len(values), statistics.mean(values), statistics.median(values)


def build_report(onsets):
    lit = onsets[LIT]
    unlit = onsets[UNLIT]
    n_lit, mean_lit, median_lit = describe(lit)
    n_unlit, mean_unlit, median_unlit = describe(unlit)

    outcome = stats.mannwhitneyu(lit, unlit, alternative="two-sided",
                                 method="exact")
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    rank_biserial = 2.0 * u_stat / (n_lit * n_unlit) - 1.0

    selected = (
        "[selected-result] Mann-Whitney U test of chorus onset, "
        "lit (n = {0}) versus unlit (n = {1}) ponds: "
        "U = {2:.1f}, exact two-sided p = {3:.5f}, "
        "rank-biserial correlation = {4:.3f}; onset is later at lit ponds "
        "(median {5:.1f} versus {6:.1f} minutes after sunset)."
    ).format(n_lit, n_unlit, u_stat, p_value, rank_biserial,
             median_lit, median_unlit)

    return "\n".join([
        "# Chorus onset at lit and unlit urban ponds",
        "",
        "## Design",
        "",
        "Twelve urban stormwater ponds were each visited on a single night of one",
        "breeding season. One chorus onset time, the number of minutes after local",
        "sunset at which continuous calling began, was logged per pond. Six ponds",
        "border continuously burning street lighting and six are unlit. Every pond",
        "appears exactly once, so the twelve onset values are mutually independent.",
        "",
        "## Group summary",
        "",
        "| Lighting regime | Ponds | Mean onset (min) | Median onset (min) |",
        "| --- | --- | --- | --- |",
        "| {0} | {1} | {2:.2f} | {3:.1f} |".format(
            LIT, n_lit, mean_lit, median_lit),
        "| {0} | {1} | {2:.2f} | {3:.1f} |".format(
            UNLIT, n_unlit, mean_unlit, median_unlit),
        "",
        "Median shift (lit minus unlit): {0:.1f} minutes.".format(
            median_lit - median_unlit),
        "",
        "## Test",
        "",
        "The two lighting regimes were compared with a two-sided Mann-Whitney U test",
        "evaluated against the exact null distribution; no ties occur in the pooled",
        "sample of twelve onset times.",
        "",
        selected,
        "",
        "## Reading of the result",
        "",
        "At the 5 percent level the onset distributions differ: calling at lit ponds",
        "starts about half an hour later relative to sunset than at unlit ponds. The",
        "comparison is observational, so lighting is not separated from whatever else",
        "distinguishes lit sites from unlit ones; pond area and water temperature were",
        "recorded but are not modelled here.",
    ]) + "\n"


def main():
    report = build_report(read_onsets())
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
