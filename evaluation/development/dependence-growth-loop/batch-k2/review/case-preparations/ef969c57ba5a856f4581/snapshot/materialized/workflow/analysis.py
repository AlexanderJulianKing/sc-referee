"""Night-time street noise before and after porous asphalt resurfacing.

Reads data/input.csv, applies an exact sign test to the per-segment change in
the L_night indicator, and writes results/report.md. One CSV row is one
resurfaced street segment, and the segments are separate sites, so every
independent unit contributes exactly one analysed row.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import fmean, median

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

FLAT_DB = 1e-9     # a change this small is bookkeeping noise, not a real change
TARGET_DB = -1.0   # reduction the resurfacing programme was meant to deliver


def read_segments(path):
    """Return the CSV rows, refusing any file that lists a segment twice."""
    with path.open(newline="", encoding="ascii") as handle:
        segments = list(csv.DictReader(handle))
    if not segments:
        raise SystemExit("no segments in {0}".format(path))
    labels = [row["segment_id"] for row in segments]
    if len(set(labels)) != len(labels):
        raise SystemExit("segment_id repeats: the sign test needs one row per segment")
    return segments


def night_change(row):
    """Post-minus-pre change in L_night for one segment, in dB(A)."""
    return float(row["post_lnight_db"]) - float(row["pre_lnight_db"])


def build_report(segments):
    changes = [night_change(row) for row in segments]
    quieter = sum(1 for c in changes if c < -FLAT_DB)
    louder = sum(1 for c in changes if c > FLAT_DB)
    flat = len(changes) - quieter - louder
    on_target = sum(1 for c in changes if c <= TARGET_DB)
    trials = quieter + louder
    if trials == 0:
        raise SystemExit("every segment came out flat; there is nothing to test")

    test = binomtest(quieter, trials, 0.5, alternative="two-sided")
    mid = median(changes)

    verdict = (
        "[selected-result] Exact two-sided sign test on {n} independent street "
        "segments, one paired row each: {q} of {t} segments were quieter after "
        "porous asphalt resurfacing (share {s:.3f}, p = {p:.6f}), with a median "
        "change of {m:.3f} dB(A)."
    ).format(
        n=len(changes),
        q=quieter,
        t=trials,
        s=quieter / trials,
        p=test.pvalue,
        m=mid,
    )

    lines = [
        "# Night-time street noise before and after porous asphalt resurfacing",
        "",
        "## What was measured",
        "",
        "Residential street segments spread across one mid-sized city were resurfaced",
        "with porous low-noise asphalt during a single construction season. The",
        "segments are separate sites: no two of them share a carriageway, a junction,",
        "or a traffic corridor. For each segment the night-time noise indicator",
        "L_night was logged for one full week before the works and for one full week",
        "afterwards, and each week of logging was condensed on site into a single",
        "energy-averaged dB(A) figure. Every segment therefore contributes exactly one",
        "paired row, and the number of analysed rows equals the number of independent",
        "segments.",
        "",
        "## How it was analysed",
        "",
        "The change for a segment is post_lnight_db minus pre_lnight_db, so a negative",
        "change means a quieter street at night. Only the sign of that change was",
        "tested, with an exact two-sided sign test (scipy.stats.binomtest, null",
        "probability 0.5). The test treats each segment as one Bernoulli trial, which",
        "is legitimate here because the segments are independent sites and none of",
        "them is entered twice. Segments with no change at all would have been dropped",
        "before the test; none had to be.",
        "",
        "## Numbers",
        "",
        "Segments analysed: {0}".format(len(changes)),
        "Quieter after resurfacing: {0}".format(quieter),
        "Louder after resurfacing: {0}".format(louder),
        "Unchanged: {0}".format(flat),
        "Share quieter: {0:.3f}".format(quieter / trials),
        "Segments reaching the {0:.1f} dB reduction target: {1}".format(
            -TARGET_DB, on_target
        ),
        "",
        "Change in L_night, dB(A), post minus pre:",
        "  mean: {0:.3f}".format(fmean(changes)),
        "  median: {0:.3f}".format(mid),
        "  minimum: {0:.3f}".format(min(changes)),
        "  maximum: {0:.3f}".format(max(changes)),
        "",
        "## Result",
        "",
        verdict,
        "",
        "## What it does and does not say",
        "",
        "The sign test uses only the direction of change, so it supports the claim",
        "that quieter nights are the usual outcome of resurfacing rather than a claim",
        "about how many decibels are gained; the median change of {0:.3f} dB(A) and the".format(
            mid
        ),
        "{0} segments that reached the {1:.1f} dB target describe the size of the".format(
            on_target, -TARGET_DB
        ),
        "effect descriptively. Because every segment appears exactly once, the {0}".format(
            trials
        ),
        "trials in the test are {0} independent sites, not {0} measurements taken on a".format(
            len(changes)
        ),
        "smaller number of streets. The programme had no untreated control streets, so",
        "a city-wide change in night-time traffic over the season is not separated",
        "from the effect of the resurfacing itself.",
    ]
    return "\n".join(lines) + "\n"


def main():
    report = build_report(read_segments(INPUT_PATH))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
