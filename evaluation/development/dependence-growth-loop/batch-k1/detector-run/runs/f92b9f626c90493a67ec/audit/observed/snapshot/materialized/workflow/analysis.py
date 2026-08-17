"""Kaldbekk fen warming array: does open-top warming raise mesocosm methane flux?

Reads the long-format campaign file data/input.csv, collapses the repeated campaigns of
each mesocosm into a single analysed value per mesocosm, and writes results/report.md.
"""

from __future__ import annotations

import csv
import statistics
from collections import OrderedDict
from pathlib import Path

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COLUMN = "mesocosm_id"
GROUP_COLUMN = "treatment"
FLUX_COLUMN = "ch4_flux_mg_m2_h"
AMBIENT = "ambient"
WARMED = "warmed"


def read_campaign_records(path):
    """Return every stored chamber campaign as a dict, in file order."""
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def collapse_to_mesocosms(records):
    """Average each mesocosm's repeated campaigns into a single analysed value."""
    series = OrderedDict()
    treatments = {}
    for record in records:
        unit = record[UNIT_COLUMN]
        group = record[GROUP_COLUMN]
        if treatments.setdefault(unit, group) != group:
            raise ValueError("mesocosm " + unit + " carries two treatment labels")
        series.setdefault(unit, []).append(float(record[FLUX_COLUMN]))
    collapsed = OrderedDict()
    for unit, fluxes in series.items():
        collapsed[unit] = (treatments[unit], statistics.fmean(fluxes), len(fluxes))
    return collapsed


def group_means(collapsed, label):
    """Mesocosm-level means for one treatment arm, one value per mesocosm."""
    return [mean for treatment, mean, _ in collapsed.values() if treatment == label]


def build_report(records, collapsed):
    counts = sorted({n for _, _, n in collapsed.values()})
    if len(counts) != 1:
        raise ValueError("mesocosms differ in campaign count; the design is unbalanced")
    per_mesocosm = counts[0]

    ambient = group_means(collapsed, AMBIENT)
    warmed = group_means(collapsed, WARMED)
    if len(ambient) + len(warmed) != len(collapsed):
        raise ValueError("unexpected treatment label in the campaign file")

    outcome = mannwhitneyu(warmed, ambient, alternative="two-sided", method="exact")
    ambient_median = statistics.median(ambient)
    warmed_median = statistics.median(warmed)

    lines = [
        "# Warming and methane release in a subarctic fen: mesocosm-level test",
        "",
        "## Design and data",
        "",
        "`data/input.csv` holds " + str(len(records)) + " static-chamber records from the Kaldbekk fen",
        "warming array: " + str(len(collapsed)) + " peat mesocosms, each measured on " + str(per_mesocosm) + " flux campaigns",
        "(thaw-season weeks 3, 6, 9 and 12 of 2025). Half of the mesocosms carry an open-top",
        "warming chamber and half are ambient controls; the treatment was assigned once, to the",
        "whole mesocosm, and did not change between campaigns.",
        "",
        "## Analysis",
        "",
        "The four campaign records of a mesocosm are repeated measurements of the same randomised",
        "unit, so they were averaged before any test was run. Collapsing the long-format file gives",
        str(len(collapsed)) + " mesocosm mean CH4 fluxes, exactly one per mesocosm, so no mesocosm contributes more",
        "than one value. The " + str(len(warmed)) + " warmed mesocosm means were then compared with the " + str(len(ambient)) + " ambient",
        "mesocosm means using a two-sided exact Mann-Whitney U test.",
        "",
        "## Result",
        "",
        "| Treatment | Mesocosms | Campaigns per mesocosm | Mean of mesocosm means | Median mesocosm mean |",
        "| --- | --- | --- | --- | --- |",
        "| Ambient | {0} | {1} | {2:.2f} | {3:.2f} |".format(
            len(ambient), per_mesocosm, statistics.fmean(ambient), ambient_median
        ),
        "| Warmed | {0} | {1} | {2:.2f} | {3:.2f} |".format(
            len(warmed), per_mesocosm, statistics.fmean(warmed), warmed_median
        ),
        "",
        "Fluxes are in mg CH4 per square metre per hour. The warmed median mesocosm mean exceeds",
        "the ambient median by {0:.2f} mg CH4 per square metre per hour.".format(
            warmed_median - ambient_median
        ),
        "",
        (
            "[selected-result] Exact two-sided Mann-Whitney U test on {0} mesocosm-level mean CH4 "
            "fluxes ({1} warmed vs {2} ambient, one analysed value per mesocosm): U = {3:.1f}, "
            "p = {4:.3e}; warmed mesocosms released more methane (median mesocosm mean {5:.2f} "
            "vs {6:.2f} mg CH4 per square metre per hour)."
        ).format(
            len(collapsed),
            len(warmed),
            len(ambient),
            outcome.statistic,
            outcome.pvalue,
            warmed_median,
            ambient_median,
        ),
        "",
        "## Caveats",
        "",
        "The comparison is between mesocosms, so it supports a claim about mesocosms rather than",
        "about individual chamber campaigns; the " + str(len(records)) + " campaign records were used only to estimate",
        "each mesocosm's seasonal mean flux. Within-season variation is folded into that mean and",
        "is not modelled separately, and the array covers one thaw season at a single fen.",
    ]
    return "\n".join(lines) + "\n"


def main():
    records = read_campaign_records(INPUT_PATH)
    collapsed = collapse_to_mesocosms(records)
    report = build_report(records, collapsed)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
