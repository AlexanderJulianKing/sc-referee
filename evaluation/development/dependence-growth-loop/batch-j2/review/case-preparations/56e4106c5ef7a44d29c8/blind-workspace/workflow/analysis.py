"""Screen static-chamber deployments on the Sarvisuo mire for ebullition."""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

DETECTED = "yes"


def read_deployments(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def split_counts(rows, status):
    subset = [row for row in rows if row["drainage_status"] == status]
    hits = sum(1 for row in subset if row["ebullition_detected"] == DETECTED)
    return hits, len(subset) - hits


def per_collar(rows):
    order = []
    table = {}
    for row in rows:
        collar = row["collar_id"]
        if collar not in table:
            table[collar] = {"status": row["drainage_status"], "n": 0, "hits": 0}
            order.append(collar)
        table[collar]["n"] += 1
        if row["ebullition_detected"] == DETECTED:
            table[collar]["hits"] += 1
    return [(collar, table[collar]) for collar in order]


def compose(rows):
    hit_i, miss_i = split_counts(rows, "intact")
    hit_d, miss_d = split_counts(rows, "drained")
    n_i = hit_i + miss_i
    n_d = hit_d + miss_d
    n_total = n_i + n_d
    _, p_value = fisher_exact([[hit_i, miss_i], [hit_d, miss_d]],
                              alternative="two-sided")
    odds_ratio = (hit_i * miss_d) / (miss_i * hit_d)
    collars = per_collar(rows)

    out = [
        "# Ebullition detection on intact and drained peat: Sarvisuo mire",
        "",
        "## What the table holds",
        "",
        "Each row is one static-chamber deployment scored for a visible ebullition",
        "(bubble release) event during the closure window. Deployments were made on",
        "permanent collars, and every collar was visited on more than one survey week.",
        "",
        "## Deployments by collar",
        "",
        "| collar | drainage status | deployments | with ebullition |",
        "| --- | --- | --- | --- |",
    ]
    for collar, info in collars:
        out.append(f"| {collar} | {info['status']} | {info['n']} | {info['hits']} |")
    out += [
        "",
        "## Analysis",
        "",
        f"The {n_total} deployments were cross-tabulated by drainage status and ebullition",
        "outcome, and the 2x2 table was submitted to a two-sided Fisher exact test.",
        "Every deployment row entered the table as one independent trial.",
        "",
        "|  | ebullition | no ebullition |",
        "| --- | --- | --- |",
        f"| intact | {hit_i} | {miss_i} |",
        f"| drained | {hit_d} | {miss_d} |",
        "",
        f"Detection frequency was {hit_i}/{n_i} ({100 * hit_i / n_i:.1f}%) on intact collars"
        f" and {hit_d}/{n_d} ({100 * hit_d / n_d:.1f}%) on",
        f"drained collars; the sample odds ratio is {odds_ratio:.2f}.",
        "",
        "## Result",
        "",
        f"[selected-result] Two-sided Fisher exact test on {n_total} chamber deployments:"
        f" odds ratio {odds_ratio:.2f} for ebullition on intact versus drained peat"
        f" ({hit_i}/{n_i} against {hit_d}/{n_d} deployments), p = {p_value:.4f}.",
        "",
        f"Deployments were treated as independent trials, so the test counts {n_total} rows",
        f"across the {len(collars)} collars that produced them.",
    ]
    return "\n".join(out) + "\n"


def main():
    rows = read_deployments(INPUT_PATH)
    report = compose(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
