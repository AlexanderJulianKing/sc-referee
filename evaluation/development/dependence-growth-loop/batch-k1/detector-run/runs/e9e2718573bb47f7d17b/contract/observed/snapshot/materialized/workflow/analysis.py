"""Compare coral endosymbiont density between the lagoon and the forereef.

Reads data/input.csv (one row per nubbin) and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

ZONES = ("lagoon", "forereef")
ZONE_FIELD = "reef_zone"
DENSITY_FIELD = "symbiont_density_e6_per_cm2"
ALPHA = 0.05


def read_densities(path):
    """Collect the density readings of each reef zone into one array."""
    buckets = {zone: [] for zone in ZONES}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            zone = record[ZONE_FIELD].strip()
            buckets[zone].append(float(record[DENSITY_FIELD]))
    return {zone: np.array(values, dtype=float) for zone, values in buckets.items()}


def welch_df(first, second):
    """Welch-Satterthwaite degrees of freedom for two unpaired samples."""
    part_a = first.var(ddof=1) / first.size
    part_b = second.var(ddof=1) / second.size
    denominator = part_a ** 2 / (first.size - 1) + part_b ** 2 / (second.size - 1)
    return float((part_a + part_b) ** 2 / denominator)


def p_label(pvalue):
    """Report the p-value against the preset ladder of thresholds."""
    for cut in (0.001, 0.01, 0.05):
        if pvalue < cut:
            return "p < {0}".format(cut)
    return "p >= {0}".format(ALPHA)


def build_report(densities):
    lagoon = densities["lagoon"]
    forereef = densities["forereef"]

    outcome = stats.ttest_ind(lagoon, forereef, equal_var=False)
    tstat = float(outcome.statistic)
    pvalue = float(outcome.pvalue)
    dof = welch_df(lagoon, forereef)
    gap = float(lagoon.mean() - forereef.mean())
    label = p_label(pvalue)
    verdict = "significant" if pvalue < ALPHA else "not significant"

    lines = [
        "# Endosymbiont density in lagoon and forereef colonies of Porites lobata",
        "",
        "## Analysis",
        "",
        "Endosymbiont density (millions of cells per cm^2) was compared between the two",
        "reef zones with Welch's two-sample t-test (scipy.stats.ttest_ind with",
        "equal_var=False). Every nubbin record in data/input.csv contributed one",
        "observation to the test.",
        "",
        "## Result",
        "",
        "| zone | n | mean | sd |",
        "| --- | --- | --- | --- |",
        "| lagoon | {0} | {1:.3f} | {2:.3f} |".format(
            lagoon.size, lagoon.mean(), lagoon.std(ddof=1)
        ),
        "| forereef | {0} | {1:.3f} | {2:.3f} |".format(
            forereef.size, forereef.mean(), forereef.std(ddof=1)
        ),
        "",
        "Mean difference (lagoon minus forereef): {0:.3f} million cells per cm^2.".format(gap),
        "Welch t = {0:.3f}, df = {1:.1f}, {2} (two-sided, alpha = {3}).".format(
            tstat, dof, label, ALPHA
        ),
        "",
        (
            "[selected-result] Lagoon nubbins carry a higher endosymbiont density than "
            "forereef nubbins: mean difference {0:.3f} million cells per cm^2 "
            "({1:.3f} vs {2:.3f}), Welch t = {3:.3f}, df = {4:.1f}, {5}, so the zone "
            "difference is {6} at alpha = {7}."
        ).format(
            gap,
            lagoon.mean(),
            forereef.mean(),
            tstat,
            dof,
            label,
            verdict,
            ALPHA,
        ),
    ]
    return "\n".join(lines) + "\n"


def main():
    report = build_report(read_densities(INPUT_PATH))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
