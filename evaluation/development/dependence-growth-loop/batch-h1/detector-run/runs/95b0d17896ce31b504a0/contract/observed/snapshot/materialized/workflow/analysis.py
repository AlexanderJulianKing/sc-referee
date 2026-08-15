"""Circling direction at nest departure in solitary mason bees.

One nesting female per meadow patch, one row per female.  The departures scored
for a bee are pooled inside that bee into a single majority-direction call, so
the binomial test sees exactly one value from each independent bee.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
ALPHA = 0.05
NULL_SHARE = 0.5


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("no bees found in " + str(path))
    return rows


def majority_call(row: dict[str, str]) -> str:
    scored = int(row["departures_scored"])
    clockwise = int(row["clockwise_departures"])
    counterclockwise = scored - clockwise
    if counterclockwise < 0:
        raise ValueError("impossible counts for bee " + row["bee_id"])
    if clockwise == counterclockwise:
        raise ValueError("tied bee has no majority: " + row["bee_id"])
    return "clockwise" if clockwise > counterclockwise else "counterclockwise"


def main() -> None:
    rows = read_rows(INPUT_PATH)
    if len({row["bee_id"] for row in rows}) != len(rows):
        raise ValueError("bee_id must identify exactly one row")

    calls = [majority_call(row) for row in rows]
    n_bees = len(calls)
    n_clockwise = calls.count("clockwise")
    departures = sum(int(row["departures_scored"]) for row in rows)

    test = binomtest(n_clockwise, n_bees, NULL_SHARE, alternative="two-sided")
    share = n_clockwise / n_bees
    verdict = "rejected" if test.pvalue < ALPHA else "not rejected"

    lines = [
        "# Circling direction at nest departure in solitary mason bees",
        "",
        "## Design",
        "",
        f"Each of the {n_bees} bees in `data/input.csv` occupied its own meadow patch and",
        f"contributes exactly one row. The {departures} scored departures are not analysed",
        "individually: within a bee the departures are collapsed to a single majority",
        "call (clockwise or counterclockwise), so the analysed sample is one call per",
        "bee.",
        "",
        "## Analysis",
        "",
        "Exact two-sided binomial test (`scipy.stats.binomtest`) of the number of",
        f"clockwise-majority bees against a no-bias expectation of {NULL_SHARE}, alpha = {ALPHA}.",
        "",
        "## Result",
        "",
        f"- Clockwise-majority bees: {n_clockwise} of {n_bees} ({share:.3f})",
        f"- Counterclockwise-majority bees: {n_bees - n_clockwise}",
        f"- Exact two-sided p-value: {test.pvalue:.4f}",
        "",
        f"[selected-result] Exact two-sided binomial test on one majority-direction call per bee: {n_clockwise}/{n_bees} bees ({share:.3f}) circled clockwise more often than counterclockwise, p = {test.pvalue:.4f}; the 50:50 no-bias null is {verdict} at alpha = {ALPHA}.",
        "",
        "The bees, not the individual departures, are the replicated units, so the",
        f"test statistic rests on {n_bees} independent observations.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
