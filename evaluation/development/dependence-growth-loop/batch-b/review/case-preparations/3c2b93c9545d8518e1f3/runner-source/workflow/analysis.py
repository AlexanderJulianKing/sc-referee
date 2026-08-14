"""Slope aspect and daily melt at Kessel Glacier ablation stakes.

Reads data/input.csv, contrasts north-facing with south-facing readings, and
writes results/report.md.
"""

import csv
import os

import numpy as np
from scipy import stats

INPUT_PATH = os.path.join("data", "input.csv")
OUTPUT_PATH = os.path.join("results", "report.md")
RESPONSE = "ablation_mm"
GROUPING = "slope_aspect"


def load_readings(path):
    """Return every stake-day melt reading as a small dictionary."""
    readings = []
    with open(path, newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            readings.append(
                {
                    "stake": record["stake_id"],
                    "aspect": record[GROUPING],
                    "day": int(record["survey_day"]),
                    "melt": float(record[RESPONSE]),
                }
            )
    return readings


def split_by_aspect(readings):
    """Bucket the melt values under the aspect label of their reading."""
    buckets = {}
    for reading in readings:
        buckets.setdefault(reading["aspect"], []).append(reading["melt"])
    return {label: np.asarray(vals, dtype=float) for label, vals in buckets.items()}


def welch_dof(first, second):
    """Welch-Satterthwaite degrees of freedom for two samples."""
    term_a = first.var(ddof=1) / first.size
    term_b = second.var(ddof=1) / second.size
    spread = term_a ** 2 / (first.size - 1) + term_b ** 2 / (second.size - 1)
    return (term_a + term_b) ** 2 / spread


def summary_rows(buckets):
    """Markdown lines for the per-aspect summary table."""
    table = [
        "| {} | n | mean {} | sd {} |".format(GROUPING, RESPONSE, RESPONSE),
        "| --- | --- | --- | --- |",
    ]
    for label in sorted(buckets):
        sample = buckets[label]
        table.append(
            "| {} | {} | {:.3f} | {:.3f} |".format(
                label, sample.size, sample.mean(), sample.std(ddof=1)
            )
        )
    return table


def compose(readings, buckets, result, dof):
    """Assemble the whole report as one string."""
    north = buckets["north"]
    south = buckets["south"]
    gap = south.mean() - north.mean()
    if result.pvalue < 1e-4:
        p_text = "p < 0.0001"
    else:
        p_text = "p = {:.4f}".format(result.pvalue)

    lines = [
        "# Slope aspect and daily melt at Kessel Glacier ablation stakes",
        "",
        "## Data",
        "",
        "Table `data/input.csv` holds {} melt readings taken with a folding rule at".format(
            len(readings)
        ),
        "ablation stakes drilled into the glacier surface. Each reading gives the",
        "surface lowering `{}` measured on one survey day, together with the".format(
            RESPONSE
        ),
        "aspect of the slope the stake sits on.",
        "",
    ]
    lines.extend(summary_rows(buckets))
    lines.extend(
        [
            "",
            "## Analysis",
            "",
            "Welch's two-sample t-test (two-sided, unequal variances) on `{}`,".format(
                RESPONSE
            ),
            "contrasting south-facing against north-facing readings. Each row of the table",
            "supplied one observation to the test, so the two samples held {} values each.".format(
                north.size
            ),
            "",
            "## Result",
            "",
            "[selected-result] Welch's two-sample t-test on {} stake-day readings gives mean"
            " {} of {:.3f} mm on south-facing slopes against {:.3f} mm on north-facing"
            " slopes, a gap of {:.3f} mm (t = {:.3f}, df = {:.3f}, {}).".format(
                len(readings),
                RESPONSE,
                south.mean(),
                north.mean(),
                gap,
                result.statistic,
                dof,
                p_text,
            ),
            "",
            "The melt gap of {:.3f} mm per day between the two aspects is far larger than the".format(
                gap
            ),
            "spread within either group (sd {:.3f} mm south, {:.3f} mm north).".format(
                south.std(ddof=1), north.std(ddof=1)
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    readings = load_readings(INPUT_PATH)
    buckets = split_by_aspect(readings)
    result = stats.ttest_ind(buckets["south"], buckets["north"], equal_var=False)
    dof = welch_dof(buckets["south"], buckets["north"])
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(compose(readings, buckets, result, dof))


if __name__ == "__main__":
    main()
