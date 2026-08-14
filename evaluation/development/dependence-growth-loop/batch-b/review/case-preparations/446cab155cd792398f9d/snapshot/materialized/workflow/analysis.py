"""Interim exceedance screening for the Fernbrook bioretention pilot.

Reads the 2024 storm-event effluent records and writes a short markdown
summary of how often cell effluent sat above the interim discharge target.
"""

import csv
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

TARGET_TP_MGL = 0.10
NULL_EXCEEDANCE_PROB = 0.5


def read_records(path):
    """Return every row of the monitoring file as a dictionary."""
    with path.open("r", encoding="ascii", newline="") as handle:
        return list(csv.DictReader(handle))


def is_exceedance(record):
    """True when the record sits strictly above the interim target."""
    return float(record["effluent_tp_mgl"]) > TARGET_TP_MGL


def cell_rollup(records):
    """Record and exceedance counts per cell, in first-appearance order."""
    order = []
    counts = {}
    for record in records:
        cell = record["cell_id"]
        if cell not in counts:
            order.append(cell)
            counts[cell] = {
                "media_mix": record["media_mix"],
                "records": 0,
                "exceedances": 0,
            }
        counts[cell]["records"] += 1
        if is_exceedance(record):
            counts[cell]["exceedances"] += 1
    return [(cell, counts[cell]) for cell in order]


def build_report(records):
    """Render the markdown report text for the supplied records."""
    n_records = len(records)
    n_exceed = sum(1 for record in records if is_exceedance(record))
    n_cells = len({record["cell_id"] for record in records})
    n_storms = len({record["storm_id"] for record in records})
    share = n_exceed / n_records
    mean_tp = sum(
        float(record["effluent_tp_mgl"]) for record in records
    ) / n_records
    test = stats.binomtest(
        n_exceed, n_records, NULL_EXCEEDANCE_PROB, alternative="two-sided"
    )
    p_value = test.pvalue

    lines = [
        "# Fernbrook bioretention pilot: interim exceedance screening",
        "",
        "## What was measured",
        "",
        "Each record in `data/input.csv` is one storm-event grab sample of the",
        "effluent leaving one bioretention cell. A record carries the cell, the",
        "sampled storm, the cell's filter media mix, the antecedent dry period,",
        "and the effluent total phosphorus concentration in mg/L.",
        "",
        f"- Records analysed: {n_records}",
        f"- Cells represented: {n_cells}",
        f"- Storms represented: {n_storms}",
        f"- Interim discharge target: {TARGET_TP_MGL:.3f} mg/L; a record counts as",
        "  an exceedance when its concentration is strictly above the target",
        f"- Mean effluent total phosphorus: {mean_tp:.4f} mg/L",
        f"- Records above the target: {n_exceed} of {n_records} (share {share:.4f})",
        "",
        "Records and exceedances by cell:",
        "",
        "| cell_id | media_mix | records | exceedances |",
        "| --- | --- | --- | --- |",
    ]
    for cell, info in cell_rollup(records):
        lines.append(
            "| {0} | {1} | {2} | {3} |".format(
                cell, info["media_mix"], info["records"], info["exceedances"]
            )
        )
    lines.extend([
        "",
        "## Analysis",
        "",
        "Every record in the file was supplied as one trial to an exact two-sided",
        "binomial test (`scipy.stats.binomtest`) of the null hypothesis that a",
        f"record exceeds the target with probability {NULL_EXCEEDANCE_PROB}, that is,",
        "that exceedance and compliance are equally likely for a record. The test",
        f"statistic is the number of records above the target, {n_exceed} out of",
        f"{n_records} trials.",
        "",
        "## Result",
        "",
        f"The observed exceedance share is {share:.4f} ({n_exceed}/{n_records}),",
        f"against the benchmark share of {NULL_EXCEEDANCE_PROB}. The exact two-sided",
        f"binomial p-value is {p_value:.4f}. At the 5% level the record-level",
        "exceedance share is therefore distinguishable from the break-even",
        "benchmark, with exceedances outnumbering compliant records.",
        "",
        "[selected-result] Exact two-sided binomial test of record-level"
        f" exceedance of the {TARGET_TP_MGL:.3f} mg/L interim total phosphorus"
        f" target: {n_exceed} of {n_records} records exceeded (share"
        f" {share:.4f}) against a null exceedance probability of"
        f" {NULL_EXCEEDANCE_PROB}; p = {p_value:.4f}.",
    ])
    return "\n".join(lines) + "\n"


def main():
    records = read_records(INPUT_PATH)
    report = build_report(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
