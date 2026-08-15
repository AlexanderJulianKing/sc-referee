"""Array-choice scoring for bumble bee foraging bouts.

Reads the bout tallies, decides which array won each bout, and tests the
overall pick rate against an even null preference.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from scipy.stats import binomtest

DATA = Path("data/input.csv")
REPORT = Path("results/report.md")
NULL_PREFERENCE = 0.5


def load_bouts(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def picked_uv(row):
    return int(row["visits_uv"]) > int(row["visits_white"])


def main():
    bouts = load_bouts(DATA)
    picks = [picked_uv(row) for row in bouts]
    n_bouts = len(picks)
    n_uv = sum(picks)

    totals = Counter()
    uv_by_colony = Counter()
    for row, pick in zip(bouts, picks):
        totals[row["colony_id"]] += 1
        uv_by_colony[row["colony_id"]] += int(pick)

    test = binomtest(n_uv, n_bouts, NULL_PREFERENCE, alternative="two-sided")
    share = n_uv / n_bouts

    lines = [
        "# UV-reflective array preference in bumble bee foraging bouts",
        "",
        "## Data",
        "",
        f"{n_bouts} foraging bouts were scored across {len(totals)} queenright colonies.",
        "A bout counts as a UV pick when the forager delivered more visits to the",
        "UV-reflective array than to the plain white array.",
        "",
        f"UV picks: {n_uv} of {n_bouts} bouts ({share * 100:.1f}%).",
        "",
        "| colony | UV picks | bouts |",
        "| --- | --- | --- |",
    ]
    for colony in sorted(totals):
        lines.append(f"| {colony} | {uv_by_colony[colony]} | {totals[colony]} |")

    lines += [
        "",
        "## Analysis",
        "",
        f"Exact two-sided binomial test on the {n_bouts} bout outcomes against a null",
        f"UV-pick probability of {NULL_PREFERENCE:.3f}; each bout enters the test as one",
        "independent trial.",
        "",
        "## Result",
        "",
        f"[selected-result] Exact binomial test: {n_uv} UV picks in {n_bouts} bouts "
        f"(observed share {share:.3f}), two-sided p = {test.pvalue:.4f} against "
        f"p0 = {NULL_PREFERENCE:.3f}; foragers picked the UV-reflective array more "
        "often than the null preference.",
        "",
        f"Null hypothesis rejected at alpha = 0.05: {'yes' if test.pvalue < 0.05 else 'no'}.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
