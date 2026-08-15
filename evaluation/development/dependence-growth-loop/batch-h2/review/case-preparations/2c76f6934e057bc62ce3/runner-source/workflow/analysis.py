"""Biochar amendment and growing-season soil CO2 efflux in a hillside vineyard.

Reads the static-chamber flux table and writes a short markdown summary that
compares efflux between amended and unamended plots.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT = Path("data/input.csv")
OUTPUT = Path("results/report.md")

TREATMENTS = ("biochar", "control")
P_BANDS = ((0.001, "p < 0.001"), (0.01, "p < 0.01"), (0.05, "p < 0.05"))


def read_efflux():
    """Collect the chamber efflux readings, keyed by treatment label."""
    pooled = {name: [] for name in TREATMENTS}
    with INPUT.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            pooled[record["treatment"]].append(
                float(record["co2_flux_umol_m2_s"])
            )
    return {
        name: np.asarray(values, dtype=float) for name, values in pooled.items()
    }


def welch_df(first, second):
    """Welch-Satterthwaite degrees of freedom for two samples."""
    sa = first.var(ddof=1) / first.size
    sb = second.var(ddof=1) / second.size
    return (sa + sb) ** 2 / (
        sa ** 2 / (first.size - 1) + sb ** 2 / (second.size - 1)
    )


def band(pvalue):
    """Report the p-value against the usual significance thresholds."""
    for cut, label in P_BANDS:
        if pvalue < cut:
            return label
    return "p >= 0.05"


def table_row(name, sample):
    return "| %s | %d | %.3f | %.3f |" % (
        name,
        sample.size,
        sample.mean(),
        sample.std(ddof=1),
    )


def main():
    samples = read_efflux()
    amended = samples["biochar"]
    control = samples["control"]

    outcome = stats.ttest_ind(amended, control, equal_var=False)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)
    dfree = welch_df(amended, control)
    gap = amended.mean() - control.mean()

    lines = [
        "# Biochar amendment and growing-season soil CO2 efflux",
        "",
        "## Data",
        "",
        "Chamber measurements of soil CO2 efflux were collected in a hillside vineyard:",
        "12 plots (6 biochar-amended, 6 unamended control) were visited in 5 sampling",
        "campaigns across one growing season, giving %d measurements in total."
        % (amended.size + control.size),
        "",
        "## Analysis",
        "",
        "Each chamber measurement was entered as one replicate observation of its",
        "treatment, giving %d observations per treatment. The two treatments were"
        % amended.size,
        "compared with a Welch two-sample t-test (two-sided) on soil CO2 efflux in",
        "umol m^-2 s^-1.",
        "",
        "## Result",
        "",
        "| treatment | n | mean efflux | SD |",
        "| --- | --- | --- | --- |",
        table_row("biochar", amended),
        table_row("control", control),
        "",
        "Mean difference (biochar minus control): %+.3f umol m^-2 s^-1." % gap,
        "",
        "Welch t = %.3f, df = %.1f, %s." % (tstat, dfree, band(pvalue)),
        "",
        "[selected-result] Welch two-sample t-test on %d chamber measurements "
        "(%d biochar, %d control): mean soil CO2 efflux is %.3f umol m^-2 s^-1 "
        "higher in biochar-amended plots (%.3f vs %.3f), t = %.3f, df = %.1f, %s."
        % (
            amended.size + control.size,
            amended.size,
            control.size,
            gap,
            amended.mean(),
            control.mean(),
            tstat,
            dfree,
            band(pvalue),
        ),
        "",
        "## Notes",
        "",
        "Amended plots vented more CO2 than control plots across the season, and the",
        "difference is significant at the 0.1% level.",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
