"""Boreal fen drainage experiment: collar-level methane flux comparison.

The input table stores three seasonal chamber sessions per permanent collar in
long format. The sessions of one collar are repeated measurements of the same
plot, so every collar is collapsed to a single analysed value before the two
water-table treatments are compared with an exact Mann-Whitney U test.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import fmean, median

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"
TREATMENTS = ("intact", "drained")


def read_sessions(path):
    """Group the long-format session rows by collar, preserving file order."""
    order = []
    bundles = {}
    with path.open(newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            collar = record["collar_id"]
            if collar not in bundles:
                order.append(collar)
                bundles[collar] = {
                    "treatment": record["treatment"],
                    "flux": [],
                    "depth": [],
                }
            bundles[collar]["flux"].append(float(record["ch4_flux_mg_m2_h"]))
            bundles[collar]["depth"].append(float(record["water_table_depth_cm"]))
    return [(collar, bundles[collar]) for collar in order]


def collapse_to_collars(grouped):
    """One analysed value per collar: the mean of its repeated sessions."""
    collars = []
    for collar, bundle in grouped:
        flux = bundle["flux"]
        collars.append(
            {
                "collar": collar,
                "treatment": bundle["treatment"],
                "sessions": len(flux),
                "mean_flux": fmean(flux),
                "mean_depth": fmean(bundle["depth"]),
                "flux_range": max(flux) - min(flux),
            }
        )
    return collars


def group_means(collars):
    return {
        t: [c["mean_flux"] for c in collars if c["treatment"] == t] for t in TREATMENTS
    }


def build_report(collars, test):
    n_rows = sum(c["sessions"] for c in collars)
    by_group = {t: [c for c in collars if c["treatment"] == t] for t in TREATMENTS}
    flux = {t: [c["mean_flux"] for c in rows] for t, rows in by_group.items()}
    depth = {t: [c["mean_depth"] for c in rows] for t, rows in by_group.items()}
    ranges = [c["flux_range"] for c in collars]

    n_intact = len(flux["intact"])
    n_drained = len(flux["drained"])
    cles = test.statistic / (n_intact * n_drained)
    mean_gap = fmean(flux["intact"]) - fmean(flux["drained"])
    median_gap = median(flux["intact"]) - median(flux["drained"])

    lines = [
        "# Water-table drawdown and methane efflux in a boreal fen",
        "",
        "## Design and unit of analysis",
        "",
        (
            "Twelve permanent chamber collars were installed in a boreal fen: six in "
            "intact peat and six inside an experimental drainage block. Each collar was "
            "revisited in three seasonal flux sessions, so the source table holds "
            f"{n_rows} measurement rows for {len(collars)} collars."
        ),
        "",
        (
            "The three sessions recorded for a collar are repeated measurements of the "
            "same physical collar; they share its peat profile, vegetation and "
            "microtopography and are not independent replicates of the drainage "
            "treatment. Each collar is therefore reduced to one analysed value, the mean "
            "of its session fluxes, before any test is applied. The independent unit is "
            f"the collar, so the comparison rests on {len(collars)} values, not "
            f"{n_rows}."
        ),
        "",
        "## Collar-level values",
        "",
        (
            "| collar | treatment | sessions | mean water table (cm below surface) | "
            "mean CH4 flux (mg m^-2 h^-1) | session range |"
        ),
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in collars:
        lines.append(
            "| {collar} | {treatment} | {sessions} | {depth:.2f} | {flux:.2f} | "
            "{spread:.2f} |".format(
                collar=c["collar"],
                treatment=c["treatment"],
                sessions=c["sessions"],
                depth=c["mean_depth"],
                flux=c["mean_flux"],
                spread=c["flux_range"],
            )
        )
    lines += [
        "",
        "## Group summary (collar means)",
        "",
        (
            f"- intact: n = {n_intact} collars, mean of collar means = "
            f"{fmean(flux['intact']):.2f}, median = {median(flux['intact']):.2f}, "
            f"mean water table = {fmean(depth['intact']):.2f} cm"
        ),
        (
            f"- drained: n = {n_drained} collars, mean of collar means = "
            f"{fmean(flux['drained']):.2f}, median = {median(flux['drained']):.2f}, "
            f"mean water table = {fmean(depth['drained']):.2f} cm"
        ),
        (
            f"- intact minus drained: {mean_gap:.2f} mg m^-2 h^-1 in means, "
            f"{median_gap:.2f} mg m^-2 h^-1 in medians"
        ),
        "",
        "## Test",
        "",
        (
            f"A two-sided exact Mann-Whitney U test was run on the {len(collars)} "
            "collar-level mean fluxes, six per treatment, with the collar as the "
            "independent unit. The exact null distribution is used because the group "
            "sizes are small and no collar mean is tied."
        ),
        "",
        (
            f"U = {test.statistic:.0f}, exact two-sided p = {test.pvalue:.6f}, "
            f"common-language effect size = {cles:.3f} (the probability that a randomly "
            "chosen intact collar exceeds a randomly chosen drained collar)."
        ),
        "",
        (
            "[selected-result] Collar-mean CH4 flux was higher in intact fen than in "
            f"drained fen (exact two-sided Mann-Whitney U = {test.statistic:.0f}, n = "
            f"{n_intact} vs {n_drained} collars, p = {test.pvalue:.6f}; group means "
            f"{fmean(flux['intact']):.2f} vs {fmean(flux['drained']):.2f} mg m^-2 h^-1, "
            f"difference {mean_gap:.2f})."
        ),
        "",
        "## Notes",
        "",
        (
            "Session-to-session variation within a collar is small (ranges of "
            f"{min(ranges):.2f} to {max(ranges):.2f} mg m^-2 h^-1) next to the spread "
            "between collars, so averaging the three sessions loses little information "
            "while keeping one row per independent unit in the test. Water-table depth "
            "is reported as a manipulation check and was not used in the test."
        ),
    ]
    return "\n".join(lines) + "\n"


def main():
    grouped = read_sessions(INPUT_PATH)
    collars = collapse_to_collars(grouped)
    flux = group_means(collars)
    test = mannwhitneyu(
        flux["intact"], flux["drained"], alternative="two-sided", method="exact"
    )
    report = build_report(collars, test)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
