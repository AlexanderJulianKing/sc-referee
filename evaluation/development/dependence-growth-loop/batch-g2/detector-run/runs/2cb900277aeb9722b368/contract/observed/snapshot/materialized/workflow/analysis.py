"""Fouling trial on moored sensor housings.

Reads the long-format inspection log in data/input.csv, reduces the repeated
inspections of each housing to a single fouling accumulation rate, compares the
two coatings on those per-housing rates, and writes results/report.md.
"""

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

CONTROL = "epoxy_control"
TOPCOAT = "silicone_hydrogel"

COL_W = (7, 17, 4)


def read_log(path):
    """Group the inspection log by housing, keeping (month, cover) pairs."""
    inspections = {}
    coating_of = {}
    with path.open("r", newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            housing = row["housing_id"]
            inspections.setdefault(housing, []).append(
                (float(row["month_index"]), float(row["biofilm_cover_pct"]))
            )
            coating_of[housing] = row["coating"]
    return inspections, coating_of


def accumulation_rate(records):
    """OLS slope of biofilm cover on month index, in points per month."""
    months = np.array([m for m, _ in records], dtype=float)
    cover = np.array([c for _, c in records], dtype=float)
    slope, _intercept = np.polyfit(months, cover, 1)
    return float(slope)


def welch_dof(first, second):
    """Welch-Satterthwaite degrees of freedom for two independent samples."""
    a = first.var(ddof=1) / first.size
    b = second.var(ddof=1) / second.size
    return float(
        (a + b) ** 2 / (a * a / (first.size - 1) + b * b / (second.size - 1))
    )


def row_line(cells):
    padded = (
        cells[0].ljust(COL_W[0]),
        cells[1].ljust(COL_W[1]),
        cells[2].rjust(COL_W[2]),
    )
    return "| " + " | ".join(padded) + " |"


def rule_line():
    return "|" + "|".join("-" * (width + 2) for width in COL_W) + "|"


def main():
    inspections, coating_of = read_log(INPUT_PATH)
    housings = sorted(inspections)

    visit_counts = set(len(records) for records in inspections.values())
    if len(visit_counts) != 1:
        raise ValueError("housings do not share a common inspection schedule")
    per_housing = visit_counts.pop()
    n_sessions = per_housing * len(housings)

    # One analysed number per independently moored housing.
    rate = dict((h, accumulation_rate(inspections[h])) for h in housings)
    control = np.array([rate[h] for h in housings if coating_of[h] == CONTROL])
    topcoat = np.array([rate[h] for h in housings if coating_of[h] == TOPCOAT])

    tstat, pval = stats.ttest_ind(control, topcoat, equal_var=False)
    dof = welch_dof(control, topcoat)
    diff = float(control.mean() - topcoat.mean())
    stderr = float(
        np.sqrt(
            control.var(ddof=1) / control.size + topcoat.var(ddof=1) / topcoat.size
        )
    )
    margin = float(stats.t.ppf(0.975, dof)) * stderr
    low = diff - margin
    high = diff + margin
    p_text = "p < 0.0001" if pval < 1e-4 else "p = {:.4f}".format(pval)

    lines = [
        "# Biofilm accumulation on moored sensor housings under two hull coatings",
        "",
        "## Study and data",
        "",
        "The array holds {} oceanographic sensor housings moored independently on the Kelso".format(len(housings)),
        "Bank shelf: {} finished with the yard-standard epoxy ({}) and {} with an".format(control.size, CONTROL, topcoat.size),
        "experimental silicone-hydrogel topcoat ({}). Each housing was".format(TOPCOAT),
        "photographed by a diver at four monthly inspections (month 0 to month 3) and the",
        "fraction of the housing shoulder covered by biofilm was scored from each image.",
        "The file therefore holds {} session records, {} per housing.".format(n_sessions, per_housing),
        "",
        "## Statistical approach",
        "",
        "The four inspections of a given housing are repeated measurements of the same",
        "mooring and are not independent of one another, so they were not entered into the",
        "group comparison as separate observations. Each housing was first summarised by",
        "the ordinary least-squares slope of biofilm cover on month index, that is, its",
        "fouling accumulation rate in percentage points per month. That reduction yields",
        "exactly one analysed value per independently moored housing, and the {} rates were".format(len(housings)),
        "compared between coatings with Welch's two-sample t-test for unequal variances",
        "(two-sided).",
        "",
        "## Per-housing fouling accumulation rate",
        "",
        row_line(("housing", "coating", "rate")),
        rule_line(),
    ]
    for housing in housings:
        lines.append(
            row_line(
                (housing, coating_of[housing], "{:.2f}".format(rate[housing]))
            )
        )
    lines.extend(
        [
            "",
            "Rate is in percentage points of cover per month; {} housings, one rate each.".format(len(housings)),
            "",
            "## Result",
            "",
            "Epoxy control: mean rate {:.2f} pp/month (SD {:.2f}, n = {} housings).".format(control.mean(), control.std(ddof=1), control.size),
            "Silicone-hydrogel topcoat: mean rate {:.2f} pp/month (SD {:.2f}, n = {} housings).".format(topcoat.mean(), topcoat.std(ddof=1), topcoat.size),
            "Difference (control minus topcoat): {:.2f} pp/month, 95% CI [{:.2f}, {:.2f}].".format(diff, low, high),
            "",
            "[selected-result] Welch's two-sample t-test on {} independent per-housing fouling accumulation rates ({} {} vs {} {}, one OLS slope per housing over its {} monthly inspections): t = {:.2f}, df = {:.1f}, {}; the silicone-hydrogel topcoat accumulates biofilm {:.2f} pp/month more slowly (95% CI [{:.2f}, {:.2f}]).".format(len(housings), control.size, CONTROL, topcoat.size, TOPCOAT, per_housing, tstat, dof, p_text, diff, low, high),
            "",
            "The {} session-level records were used only to estimate the within-housing slopes;".format(n_sessions),
            "no inference was drawn from them as if they were {} independent observations.".format(n_sessions),
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
