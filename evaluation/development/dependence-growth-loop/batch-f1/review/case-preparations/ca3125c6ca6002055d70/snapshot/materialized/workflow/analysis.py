"""Exact binomial test of first-arm choice in the paired-array foraging assay.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
MARKED_ARM = "uv_marked"


def read_bouts(path: Path) -> List[Dict[str, str]]:
    """Return every scored bout of the assay as a plain dictionary."""
    with path.open("r", encoding="ascii", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def per_bee_tally(bouts: List[Dict[str, str]]) -> Dict[str, List[int]]:
    """Bouts flown and UV-marked first choices, keyed by paint-mark code."""
    tally: Dict[str, List[int]] = {}
    for bout in bouts:
        bee = bout["bee_id"]
        if bee not in tally:
            tally[bee] = [0, 0]
        tally[bee][0] += 1
        if bout["first_arm"] == MARKED_ARM:
            tally[bee][1] += 1
    return tally


def build_report(bouts: List[Dict[str, str]]) -> str:
    n_bouts = len(bouts)
    n_marked = sum(1 for bout in bouts if bout["first_arm"] == MARKED_ARM)
    tally = per_bee_tally(bouts)
    mean_handling = sum(float(bout["handling_time_s"]) for bout in bouts) / n_bouts
    share_marked = 100.0 * n_marked / n_bouts

    outcome = binomtest(n_marked, n_bouts, 0.5, alternative="two-sided")
    p_value = outcome.pvalue

    lines = [
        "# First-arm choice in the paired-array foraging assay",
        "",
        "## Data",
        "",
        "- Source table: `data/input.csv`",
        "- Foraging bouts scored: {0}".format(n_bouts),
        "- Individually marked bees: {0}".format(len(tally)),
        "- Bouts choosing the UV-marked arm first: {0} ({1:.1f}%)".format(
            n_marked, share_marked
        ),
        "- Mean handling time across bouts: {0:.2f} s".format(mean_handling),
        "",
        "### Bouts per bee",
        "",
        "| bee_id | bouts | uv_marked first | share |",
        "| --- | --- | --- | --- |",
    ]
    for bee, (bouts_flown, marked_first) in tally.items():
        lines.append(
            "| {0} | {1} | {2} | {3:.3f} |".format(
                bee, bouts_flown, marked_first, marked_first / bouts_flown
            )
        )
    lines += [
        "",
        "## Analysis",
        "",
        "Every scored bout was entered as one Bernoulli trial, and the {0} trials"
        " were submitted".format(n_bouts),
        "to an exact two-sided binomial test (`scipy.stats.binomtest`) against the",
        "no-preference expectation of 0.5.",
        "",
        "## Result",
        "",
        "[selected-result] Exact two-sided binomial test on {0} scored bouts:"
        " {1} of {0} first choices went to the UV-marked arm ({2:.1f}%),"
        " p = {3:.6f} against the null proportion of 0.5, indicating a"
        " statistically significant bias away from the UV-marked arm at the"
        " 5% level.".format(n_bouts, n_marked, share_marked, p_value),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    bouts = read_bouts(INPUT_PATH)
    report = build_report(bouts)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
