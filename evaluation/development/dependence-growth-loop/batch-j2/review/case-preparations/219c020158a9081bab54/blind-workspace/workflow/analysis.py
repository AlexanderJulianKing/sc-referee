#!/usr/bin/env python3
"""Berth 7 recoating trial.

Reads the four-year gauge survey from data/input.csv, compares the corrosion
rate recorded under the two protective coating systems, and writes a short
markdown report to results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

GROUP_COL = "coating_system"
UNIT_COL = "piling_id"
RATE_COL = "corrosion_rate_um_per_yr"
ALPHA = 0.05


def read_survey(path: Path) -> list:
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def bucket(records: list, key_fn) -> dict:
    """Collect the corrosion rates under whatever key key_fn returns."""
    grouped: dict = {}
    for rec in records:
        grouped.setdefault(key_fn(rec), []).append(float(rec[RATE_COL]))
    return {key: np.asarray(vals, dtype=float) for key, vals in sorted(grouped.items())}


def main() -> None:
    records = read_survey(INPUT_PATH)
    if not records:
        raise SystemExit("data/input.csv contains no readings")

    by_coating = bucket(records, lambda r: r[GROUP_COL])
    by_piling = bucket(records, lambda r: (r[GROUP_COL], r[UNIT_COL]))

    names = list(by_coating)
    if len(names) != 2:
        raise SystemExit("expected exactly two coating systems")

    ref, alt = names
    a = by_coating[ref]
    b = by_coating[alt]

    outcome = stats.ttest_ind(a, b, equal_var=True)
    tstat = float(outcome.statistic)
    pval = float(outcome.pvalue)
    df = a.size + b.size - 2
    delta = float(a.mean() - b.mean())

    p_text = "p < 0.001" if pval < 0.001 else "p = %.3f" % pval
    verdict = "significant" if pval < ALPHA else "not significant"
    n_rows = len(records)
    n_pilings = len(by_piling)

    lines = [
        "# Berth 7 coating trial: four-year corrosion rates",
        "",
        "Source table: `data/input.csv` - %d ultrasonic gauge readings from %d pilings."
        % (n_rows, n_pilings),
        "",
        "## What was surveyed",
        "",
        "Twelve steel sheet pilings at Berth 7 were re-gauged after four years in",
        "service. Alternate pilings along the berth carry one of two protective",
        "coating systems. Every piling was gauged in the same four depth bands",
        "(0.5 m, 1.5 m, 3.0 m and 5.0 m below mean sea level), and each gauge",
        "reading is converted to a mean annual thickness loss in micrometres per",
        "year.",
        "",
        "## Reading-level summary",
        "",
        "| coating system | readings | mean rate (um/yr) | sd (um/yr) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in names:
        vals = by_coating[name]
        lines.append(
            "| %s | %d | %.2f | %.2f |"
            % (name, vals.size, vals.mean(), vals.std(ddof=1))
        )

    lines += [
        "",
        "## Piling-level means",
        "",
        "| piling | coating system | readings | mean rate (um/yr) |",
        "| --- | --- | ---: | ---: |",
    ]
    for (coat, piling), vals in by_piling.items():
        lines.append("| %s | %s | %d | %.2f |" % (piling, coat, vals.size, vals.mean()))

    lines += [
        "",
        "## Test",
        "",
        "Two-sample Student t test (equal variances assumed), one observation per",
        "gauge reading, comparing %s against %s." % (ref, alt),
        "",
        "[selected-result] Two-sample t test on %d gauge readings: %s mean %.2f um/yr"
        " vs %s mean %.2f um/yr, difference %.2f um/yr, t(%d) = %.2f, %s, %s at"
        " alpha = %.2f."
        % (
            n_rows,
            ref,
            a.mean(),
            alt,
            b.mean(),
            delta,
            df,
            tstat,
            p_text,
            verdict,
            ALPHA,
        ),
        "",
        "All %d rows were entered into the test as separate observations." % n_rows,
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
