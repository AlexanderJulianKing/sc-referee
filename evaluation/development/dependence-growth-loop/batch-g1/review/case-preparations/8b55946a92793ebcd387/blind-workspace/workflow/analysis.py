"""Seeding-density comparison for the Kilda Sound kelp growline trial.

Reads data/input.csv, compares blade elongation rates between the sparse and
dense seeding treatments, and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COL = "growline_id"
GROUP_COL = "seeding_density"
SLOT_COL = "blade_slot"
VALUE_COL = "elongation_cm_per_day"
LEVELS = ("sparse", "dense")


def read_blades(path):
    """Return every blade record in the survey file as a dictionary."""
    with path.open("r", encoding="ascii", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def p_value_phrase(pvalue):
    """Place the p-value on a fixed threshold ladder so the wording is stable."""
    for threshold in (1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 5e-2):
        if pvalue < threshold:
            return "p < %g" % threshold
    return "p = %.3f" % pvalue


def main():
    records = read_blades(INPUT_PATH)

    by_group = {level: [] for level in LEVELS}
    by_unit = {}
    for row in records:
        value = float(row[VALUE_COL])
        by_group[row[GROUP_COL]].append(value)
        by_unit.setdefault(row[UNIT_COL], {"group": row[GROUP_COL], "values": []})
        by_unit[row[UNIT_COL]]["values"].append(value)

    samples = {level: np.asarray(by_group[level], dtype=float) for level in LEVELS}
    tstat, pvalue = stats.ttest_ind(
        samples["sparse"], samples["dense"], equal_var=True
    )
    dof = samples["sparse"].size + samples["dense"].size - 2
    mean_sparse = float(samples["sparse"].mean())
    mean_dense = float(samples["dense"].mean())
    difference = mean_sparse - mean_dense
    phrase = p_value_phrase(float(pvalue))

    counts = [len(entry["values"]) for entry in by_unit.values()]

    lines = ["# Kilda Sound kelp growline seeding-density trial", ""]

    lines.append("## Data")
    lines.append("Source: %s" % INPUT_PATH.as_posix())
    lines.append("Blade records: %d" % len(records))
    lines.append("Growlines: %d" % len(by_unit))
    if min(counts) == max(counts):
        lines.append("Blade records per growline: %d" % counts[0])
    else:
        lines.append(
            "Blade records per growline: %d to %d" % (min(counts), max(counts))
        )
    lines.append("")

    lines.append("## Per-growline means")
    for unit in sorted(by_unit):
        entry = by_unit[unit]
        lines.append(
            "%s  %-6s  mean = %.2f cm/day  (n = %d)"
            % (
                unit,
                entry["group"],
                float(np.mean(entry["values"])),
                len(entry["values"]),
            )
        )
    lines.append("")

    lines.append("## Method")
    lines.append("Response: %s (blade elongation rate)." % VALUE_COL)
    lines.append("Groups: %s, sparse versus dense." % GROUP_COL)
    lines.append("Test: two-sample Student t-test with a pooled variance estimate")
    lines.append(
        "(scipy.stats.ttest_ind, equal_var=True) over the %d blade records."
        % len(records)
    )
    lines.append("")

    lines.append("## Group summaries")
    for level in LEVELS:
        sample = samples[level]
        lines.append(
            "%-7s n = %d, mean = %.2f cm/day, sd = %.3f cm/day"
            % (level + ":", sample.size, sample.mean(), sample.std(ddof=1))
        )
    lines.append("Mean difference (sparse - dense): %.2f cm/day" % difference)
    lines.append("")

    lines.append("## Result")
    lines.append("t(%d) = %.3f, %s" % (dof, float(tstat), phrase))
    lines.append("")

    lines.append(
        "[selected-result] Two-sample Student t-test over %d blade elongation "
        "records from %d growlines: sparse-seeded blades elongated %.2f cm/day "
        "faster on average than dense-seeded blades (%.2f versus %.2f cm/day), "
        "t(%d) = %.3f, %s."
        % (
            len(records),
            len(by_unit),
            difference,
            mean_sparse,
            mean_dense,
            dof,
            float(tstat),
            phrase,
        )
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
