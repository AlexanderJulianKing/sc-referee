"""Cinder Flats seed-coating trial: third-season cover-target analysis.

Reads data/input.csv (one row per trial plot) and writes results/report.md.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")
TARGET_COVER_PCT = 40.0
TREATMENTS = ("inoculant_coated", "uncoated")
DISPLAY_NAME = {
    "inoculant_coated": "Inoculant-coated seed",
    "uncoated": "Uncoated seed",
}


@dataclass(frozen=True)
class PlotRecord:
    """One trial plot, sown once and scored once."""

    plot_id: str
    treatment: str
    cover_pct: float

    def met_target(self):
        return self.cover_pct >= TARGET_COVER_PCT


def read_plots(path):
    with path.open(newline="", encoding="ascii") as handle:
        records = [
            PlotRecord(
                plot_id=row["plot_id"].strip(),
                treatment=row["treatment"].strip(),
                cover_pct=float(row["perennial_cover_pct"]),
            )
            for row in csv.DictReader(handle)
        ]
    if not records:
        raise ValueError("no plots found in " + str(path))
    plot_ids = [record.plot_id for record in records]
    if len(set(plot_ids)) != len(plot_ids):
        raise ValueError("each plot must appear exactly once")
    strays = sorted({record.treatment for record in records}.difference(TREATMENTS))
    if strays:
        raise ValueError("unexpected treatment label(s): " + ", ".join(strays))
    return records


def summarise(records, treatment):
    subset = [record for record in records if record.treatment == treatment]
    covers = [record.cover_pct for record in subset]
    hits = sum(1 for record in subset if record.met_target())
    return {
        "label": DISPLAY_NAME[treatment],
        "n": len(subset),
        "hits": hits,
        "misses": len(subset) - hits,
        "share": 100.0 * hits / len(subset),
        "mean": mean(covers),
        "median": median(covers),
    }


def build_report(records):
    coated, uncoated = (summarise(records, name) for name in TREATMENTS)
    table = [
        [coated["hits"], coated["misses"]],
        [uncoated["hits"], uncoated["misses"]],
    ]
    odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
    gap = coated["share"] - uncoated["share"]
    verdict = "significant" if p_value < 0.05 else "not significant"

    lines = [
        "# Cinder Flats seed-coating trial: third-season cover target",
        "",
        "## Design",
        "",
        f"{len(records)} abandoned dryland plots on the Cinder Flats terrace were each sown",
        "once, with the seed lot randomly assigned per plot, and each plot was scored",
        "once at the end of the third growing season. A plot contributes exactly one",
        "row, so the units entering the test are independent of one another.",
        "",
        f"## Attainment of the {TARGET_COVER_PCT:.1f}% perennial-cover target",
        "",
        "| Treatment | Plots | Met target | Below target | Share meeting target |",
        "| --- | --- | --- | --- | --- |",
    ]
    for group in (coated, uncoated):
        lines.append("| {label} | {n} | {hits} | {misses} | {share:.1f}% |".format(**group))
    lines += [
        "",
        "## Cover readings",
        "",
        "| Treatment | Mean cover (%) | Median cover (%) |",
        "| --- | --- | --- |",
    ]
    for group in (coated, uncoated):
        lines.append("| {label} | {mean:.2f} | {median:.2f} |".format(**group))
    lines += [
        "",
        "## Test and result",
        "",
        "The two seed treatments were compared with a two-sided Fisher's exact test",
        "on the 2x2 table of seed treatment by target attainment. The gap in",
        f"attainment share is {gap:.1f} percentage points in favor of the coated seed.",
        "",
        (
            "[selected-result] Two-sided Fisher's exact test on "
            f"{len(records)} independent plots (one row per plot): "
            f"{coated['hits']} of {coated['n']} inoculant-coated plots versus "
            f"{uncoated['hits']} of {uncoated['n']} uncoated plots reached the "
            f"{TARGET_COVER_PCT:.1f}% perennial-cover target; odds ratio "
            f"{odds_ratio:.2f}, p = {p_value:.4f}, {verdict} at alpha = 0.05."
        ),
        "",
        "The exact test conditions on the observed margins and assumes only that the",
        f"{len(records)} plots are independent, which the one-row-per-plot design supplies.",
    ]
    return "\n".join(lines) + "\n"


def main():
    records = read_plots(INPUT_PATH)
    report = build_report(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
