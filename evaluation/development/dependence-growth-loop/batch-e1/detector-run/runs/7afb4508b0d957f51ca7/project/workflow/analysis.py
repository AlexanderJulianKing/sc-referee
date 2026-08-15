"""Compare critical thermal maxima of high-shore and low-shore periwinkles."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
BANDS = ("high", "low")


def read_trials():
    with INPUT_PATH.open(newline="", encoding="ascii") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def split_by_band(trials):
    pooled = {band: [] for band in BANDS}
    for trial in trials:
        pooled[trial["shore_zone"]].append(float(trial["ctmax_c"]))
    return {band: np.asarray(vals, dtype=float) for band, vals in pooled.items()}


def welch_df(a, b):
    va = a.var(ddof=1) / a.size
    vb = b.var(ddof=1) / b.size
    return (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))


def show_p(pvalue):
    if pvalue < 1e-6:
        return "p < 1e-06"
    return "p = {0:.6f}".format(pvalue)


def band_row(band, values):
    return "| {0} | {1} | {2:.3f} | {3:.2f} |".format(
        band, values.size, values.mean(), values.std(ddof=1)
    )


def build_report(samples, tstat, dof, pvalue):
    high = samples["high"]
    low = samples["low"]
    gap = high.mean() - low.mean()
    verdict = (
        "[selected-result] Welch two-sample t-test on ctmax_c comparing "
        "high-shore with low-shore heat-ramp trials: "
        "t = {0:.2f}, df = {1:.2f}, {2}. High-shore snails lost righting at a "
        "mean critical thermal maximum {3:.3f} C above low-shore snails."
    ).format(tstat, dof, show_p(pvalue), gap)
    return [
        "# Critical thermal maximum of shore periwinkles across tidal bands",
        "",
        "## Data",
        "",
        "data/input.csv holds 48 heat-ramp trials on 12 individually tagged periwinkles:",
        "6 snails collected from the high-shore band and 6 from the low-shore band. Each",
        "snail was ramped on 4 separate trial days, and every ramp records the body",
        "temperature at which the snail lost its righting response (ctmax_c, in C).",
        "",
        "## Analysis",
        "",
        "Each heat-ramp trial in the table was entered as one observation and the two",
        "shore bands were compared with Welch's two-sample t-test (two-sided) on the",
        "ctmax_c column.",
        "",
        "## Result",
        "",
        "| shore band | trials | mean ctmax_c (C) | SD (C) |",
        "| --- | --- | --- | --- |",
        band_row("high", high),
        band_row("low", low),
        "",
        "Mean difference (high - low) = {0:.3f} C.".format(gap),
        "",
        verdict,
        "",
        "## Reading note",
        "",
        "The table above is the whole of the reported analysis; the shore-band contrast",
        "is stated exactly as the trial-level test returned it.",
    ]


def main():
    samples = split_by_band(read_trials())
    outcome = stats.ttest_ind(samples["high"], samples["low"], equal_var=False)
    dof = welch_df(samples["high"], samples["low"])
    lines = build_report(
        samples, float(outcome.statistic), dof, float(outcome.pvalue)
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
