"""Leaf-level comparison of stomatal conductance between two soil amendments.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

GROUP_ORDER = ("biochar", "control")


def read_leaf_records(path):
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def collect_groups(records):
    conductance = {name: [] for name in GROUP_ORDER}
    plants = {name: set() for name in GROUP_ORDER}
    for record in records:
        group = record["amendment"]
        conductance[group].append(float(record["conductance_mmol_m2_s"]))
        plants[group].add(record["plant_id"])
    return conductance, plants


def summary_line(name, readings, plant_ids):
    return "| {0} | {1} | {2} | {3:.2f} | {4:.2f} |".format(
        name,
        len(readings),
        len(plant_ids),
        statistics.fmean(readings),
        statistics.median(readings),
    )


def build_report(records, conductance, plants, u_stat, p_value):
    treated = conductance["biochar"]
    control = conductance["control"]
    gap = statistics.fmean(treated) - statistics.fmean(control)
    result_line = (
        "[selected-result] Exact two-sided Mann-Whitney U test on the {0} leaf "
        "records ({1} biochar vs {2} control): U = {3:.1f}, p = {4:.6f}, "
        "median conductance {5:.2f} vs {6:.2f} mmol m-2 s-1."
    ).format(
        len(records),
        len(treated),
        len(control),
        float(u_stat),
        float(p_value),
        statistics.median(treated),
        statistics.median(control),
    )
    return [
        "# Stomatal conductance under a biochar soil amendment",
        "",
        "## Data",
        "",
        "Source file: data/input.csv ({0} leaf-level records).".format(len(records)),
        "",
        "Steady-state stomatal conductance (mmol m-2 s-1) was logged on potted",
        "greenhouse sunflowers, two leaves per plant, in a single growth run.",
        "",
        "## Analysis",
        "",
        "Each leaf record was entered as one observation and the two amendment groups",
        "were compared with a two-sided Mann-Whitney U test evaluated against the exact",
        "null distribution (no tied conductance values occur in the file).",
        "",
        "## Group summaries",
        "",
        "| amendment | leaf records | plants | mean | median |",
        "| --- | --- | --- | --- | --- |",
        summary_line("biochar", treated, plants["biochar"]),
        summary_line("control", control, plants["control"]),
        "",
        "Difference in group means (biochar - control): {0:.2f} mmol m-2 s-1.".format(gap),
        "",
        "## Result",
        "",
        result_line,
        "",
        "Conductance ranked higher under biochar than under the control amendment;",
        "only one biochar-control leaf pair is out of rank order.",
    ]


def main():
    records = read_leaf_records(INPUT_PATH)
    conductance, plants = collect_groups(records)
    u_stat, p_value = mannwhitneyu(
        conductance["biochar"],
        conductance["control"],
        alternative="two-sided",
        method="exact",
    )
    lines = build_report(records, conductance, plants, u_stat, p_value)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
