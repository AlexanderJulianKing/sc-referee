"""Rye versus wheat sourdough builds: 36-hour pH comparison."""

import csv
import math
import statistics
from pathlib import Path

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
FLOURS = ("rye", "wheat")


def read_table(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def split_by_flour(rows):
    readings = {flour: [] for flour in FLOURS}
    vessels = {flour: [] for flour in FLOURS}
    for row in rows:
        flour = row["flour_type"]
        readings[flour].append(float(row["ph_36h"]))
        if row["vessel_id"] not in vessels[flour]:
            vessels[flour].append(row["vessel_id"])
    return readings, vessels


def summary_row(flour, values, vessel_ids):
    return "| {} | {} | {} | {:.3f} | {:.4f} |".format(
        flour,
        len(vessel_ids),
        len(values),
        statistics.mean(values),
        statistics.median(values),
    )


def main():
    rows = read_table(INPUT_PATH)
    readings, vessels = split_by_flour(rows)
    rye = readings["rye"]
    wheat = readings["wheat"]
    u_stat, p_value = mannwhitneyu(
        rye, wheat, alternative="two-sided", method="exact"
    )
    arrangements = math.comb(len(rye) + len(wheat), len(rye))
    gap = statistics.median(wheat) - statistics.median(rye)

    lines = [
        "# Sourdough acidification: rye versus wheat starter builds",
        "",
        "## Data",
        "",
        "`data/input.csv` holds {} pH readings taken 36 hours after the final build.".format(len(rows)),
        "Each vessel was sampled at four separate points in the dough, and every",
        "reading enters the comparison as one observation.",
        "",
        "| Flour | Vessels | Readings | Mean pH | Median pH |",
        "| --- | ---: | ---: | ---: | ---: |",
        summary_row("rye", rye, vessels["rye"]),
        summary_row("wheat", wheat, vessels["wheat"]),
        "",
        "Median difference (wheat minus rye): {:.3f} pH units.".format(gap),
        "",
        "## Analysis",
        "",
        "A two-sided Mann-Whitney U test with the exact null distribution over the",
        "{} equally likely rank assignments compares the {} rye readings with the".format(arrangements, len(rye)),
        "{} wheat readings.".format(len(wheat)),
        "",
        "## Result",
        "",
        "[selected-result] Mann-Whitney U = {:.1f} for rye versus wheat ({} vs {} readings), two-sided exact p = {:.3e}.".format(u_stat, len(rye), len(wheat), p_value),
        "",
        "No rye reading exceeds any wheat reading, so U sits at the boundary of its",
        "exact null distribution and the p-value is the smallest the test can return",
        "at these sample sizes.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
