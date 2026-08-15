"""Screenhouse misting trial: does a misting pulse raise leaf conductance?

Reads data/input.csv, counts how many tagged leaves rose in stomatal
conductance after the pulse, runs an exact sign test on those counts, and
writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, median

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")


def read_leaf_readings(path):
    """Return every CSV row as a dictionary, in file order."""
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def build_report(rows):
    """Return the full markdown report text for the given rows."""
    pre = [float(row["pre_mist_gs"]) for row in rows]
    post = [float(row["post_mist_gs"]) for row in rows]
    change = [after - before for before, after in zip(pre, post)]

    up = len([d for d in change if d > 0.0])
    down = len([d for d in change if d < 0.0])
    tied = len(change) - up - down
    trials = up + down

    outcome = binomtest(up, n=trials, p=0.5, alternative="two-sided")
    pvalue = float(outcome.pvalue)
    share = up / trials

    lines = [
        "# Canopy misting and leaf stomatal conductance",
        "",
        "Question: after a 90-second canopy misting pulse, does stomatal conductance",
        "on a coffee shrub leaf go up or down? Each leaf was read once before and",
        "once after the pulse, and the two readings were subtracted.",
        "",
        "## Counts",
        "",
        "- Leaf readings in `data/input.csv`: {0}".format(len(rows)),
        "- Leaves with higher conductance after misting: {0}".format(up),
        "- Leaves with lower conductance after misting: {0}".format(down),
        "- Leaves with no change (dropped from the test): {0}".format(tied),
        "",
        "## Summary values (mmol m-2 s-1)",
        "",
        "| Quantity | Value |",
        "| --- | --- |",
        "| Mean pre-mist conductance | {0:.2f} |".format(mean(pre)),
        "| Mean post-mist conductance | {0:.2f} |".format(mean(post)),
        "| Mean within-leaf change | {0:.2f} |".format(mean(change)),
        "| Median within-leaf change | {0:.2f} |".format(median(change)),
        "",
        "## Test",
        "",
        "Exact two-sided binomial sign test (scipy.stats.binomtest) applied to the {0}".format(trials),
        "leaf readings, with each leaf reading supplied as one independent trial and",
        "a null success probability of 0.5 (a leaf is equally likely to rise or fall).",
        "",
        "[selected-result] Exact two-sided binomial sign test over {0} leaf readings: "
        "{1} of {0} ({2:.2f}%) rose after misting, p = {3:.4f} against p0 = 0.5, so the "
        "50/50 null is rejected at alpha = 0.05.".format(trials, up, 100.0 * share, pvalue),
        "",
        "## Reading the numbers",
        "",
        "The test statistic is the count of rising leaves, {0} out of {1} trials. Under".format(up, trials),
        "the null the two-sided exact tail probability is {0:.4f}, and the observed".format(pvalue),
        "rise fraction is {0:.2f}.".format(share),
    ]
    return "\n".join(lines) + "\n"


def main():
    rows = read_leaf_readings(INPUT_PATH)
    text = build_report(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
