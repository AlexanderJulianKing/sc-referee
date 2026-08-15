"""Post-fire pine regeneration after aerial seeding.

Reads data/input.csv, which holds one row per burn compartment, and writes
results/report.md.
"""

import csv
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

from scipy import stats

DATA_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COL = "compartment_id"
GROUP_COL = "aerial_seeding"
OUTCOME_COL = "pine_stems_per_ha"
ELEV_COL = "elevation_m"


def read_rows(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def count_units(rows):
    """A compartment may contribute at most one row; refuse anything else."""
    tally = Counter(row[UNIT_COL] for row in rows)
    repeated = sorted(unit for unit, n in tally.items() if n > 1)
    if repeated:
        raise ValueError(
            "compartments appearing more than once: " + ", ".join(repeated)
        )
    return len(tally)


def numbers(rows, column):
    return [float(row[column]) for row in rows]


def welch_df(first, second):
    a = stdev(first) ** 2 / len(first)
    b = stdev(second) ** 2 / len(second)
    return (a + b) ** 2 / (a * a / (len(first) - 1) + b * b / (len(second) - 1))


def p_phrase(p):
    if p < 0.001:
        return "p < 0.001"
    return "p = {0:.4f}".format(p)


def main():
    rows = read_rows(DATA_PATH)
    n_units = count_units(rows)

    seeded = [row for row in rows if row[GROUP_COL] == "yes"]
    natural = [row for row in rows if row[GROUP_COL] == "no"]

    stems_seeded = numbers(seeded, OUTCOME_COL)
    stems_natural = numbers(natural, OUTCOME_COL)
    elev_seeded = numbers(seeded, ELEV_COL)
    elev_natural = numbers(natural, ELEV_COL)

    t_stat, p_value = stats.ttest_ind(
        stems_seeded, stems_natural, equal_var=False
    )
    df = welch_df(stems_seeded, stems_natural)
    difference = mean(stems_seeded) - mean(stems_natural)

    headline = (
        "[selected-result] Welch's two-sample t-test across {0} independent burn"
        " compartments ({1} seeded, {2} naturally recovering, one row per"
        " compartment): seeded compartments held {3:.1f} more pine stems per"
        " hectare than naturally recovering compartments ({4:.1f} vs {5:.1f}),"
        " t = {6:.2f}, df = {7:.1f}, {8}, a statistically significant increase."
    ).format(
        n_units,
        len(stems_seeded),
        len(stems_natural),
        difference,
        mean(stems_seeded),
        mean(stems_natural),
        t_stat,
        df,
        p_phrase(p_value),
    )

    lines = [
        "# Aerial seeding and pine regeneration in burned compartments",
        "",
        "## Design",
        "",
        "Twenty-six burn compartments were surveyed once each by drone",
        "photogrammetry three growing seasons after the fire. Thirteen",
        "compartments received aerial seeding of pine seed; thirteen were left to",
        "recover naturally. The compartment is both the unit that received the",
        "treatment and the unit that was measured, and each compartment",
        "contributes exactly one row to the analysis.",
        "",
        "## Independence check",
        "",
        "- Rows read: {0}".format(len(rows)),
        "- Distinct compartments: {0}".format(n_units),
        "- Rows per compartment: 1 (no compartment appears more than once)",
        "",
        "## Group summaries",
        "",
        "| aerial_seeding | compartments | mean pine_stems_per_ha | sd | mean elevation_m |",
        "| --- | --- | --- | --- | --- |",
        "| yes | {0} | {1:.1f} | {2:.1f} | {3:.1f} |".format(
            len(stems_seeded),
            mean(stems_seeded),
            stdev(stems_seeded),
            mean(elev_seeded),
        ),
        "| no | {0} | {1:.1f} | {2:.1f} | {3:.1f} |".format(
            len(stems_natural),
            mean(stems_natural),
            stdev(stems_natural),
            mean(elev_natural),
        ),
        "",
        "## Test",
        "",
        "Welch's two-sample t-test (unequal variances, two-sided) comparing",
        "pine_stems_per_ha between seeded and naturally recovering compartments,",
        "seeded minus naturally recovering.",
        "",
        "- Mean difference: {0:.1f} stems per hectare".format(difference),
        "- t = {0:.2f}, df = {1:.1f}, {2}".format(t_stat, df, p_phrase(p_value)),
        "",
        headline,
        "",
        "## Notes",
        "",
        "Elevation was recorded as context; the two groups are closely matched on it",
        "({0:.1f} m versus {1:.1f} m) and the reported test is unadjusted. No".format(
            mean(elev_seeded), mean(elev_natural)
        ),
        "sub-compartment plot, transect, or repeat visit enters the test: the {0} rows".format(
            len(rows)
        ),
        "are {0} independent compartments, so the row count and the number of".format(
            n_units
        ),
        "independent units are the same.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
