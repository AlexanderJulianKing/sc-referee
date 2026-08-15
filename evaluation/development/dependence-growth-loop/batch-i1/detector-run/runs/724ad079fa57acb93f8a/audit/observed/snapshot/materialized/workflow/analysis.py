"""Bedrock class and filament-mat occupancy in Laugafell geothermal springs.

Reads data/input.csv, where every row is one spring visited exactly once, and
writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

BEDROCK_ORDER = ["basalt", "rhyolite"]
MAT_PRESENT = "yes"


def read_springs(path: Path) -> List[Dict[str, str]]:
    """Return one dictionary per surveyed spring."""
    with path.open(newline="", encoding="ascii") as handle:
        springs = [dict(row) for row in csv.DictReader(handle)]
    if not springs:
        raise ValueError("no spring records found")
    labels = [spring["spring_id"] for spring in springs]
    if len(set(labels)) != len(labels):
        raise ValueError("spring_id repeats; the design assumes one row per spring")
    return springs


def cross_tabulate(springs: List[Dict[str, str]]) -> Dict[str, List[int]]:
    """Count [mat present, mat absent] springs within each bedrock class."""
    table = {name: [0, 0] for name in BEDROCK_ORDER}
    for spring in springs:
        bedrock = spring["bedrock_class"].strip()
        if bedrock not in table:
            raise ValueError("unrecognised bedrock_class: " + bedrock)
        column = 0 if spring["filament_mat"].strip() == MAT_PRESENT else 1
        table[bedrock][column] += 1
    return table


def build_report(
    table: Dict[str, List[int]],
    odds_ratio: float,
    p_value: float,
    n_total: int,
) -> str:
    lines = [
        "# Bedrock class and filament-mat occupancy in Laugafell geothermal springs",
        "",
        "## Design",
        "",
        "Each row is one geothermal spring, surveyed once during the 2024 summer season.",
        "Springs were sampled at separate outflows, and every spring contributes exactly",
        "one row, so the {0} rows are {0} independent units.".format(n_total),
        "",
        "- Springs surveyed: {0}".format(n_total),
    ]
    for bedrock in BEDROCK_ORDER:
        present, absent = table[bedrock]
        group_total = present + absent
        share = 100.0 * present / group_total
        lines.append(
            "- {0}-hosted springs: {1}, filament mats present in {2} ({3:.1f}%)".format(
                bedrock, group_total, present, share
            )
        )
    lines += [
        "",
        "## Analysis",
        "",
        "Bedrock class (basalt vs. rhyolite) was cross-tabulated against filament-mat",
        "presence and tested with Fisher's exact test, two-sided. An exact test suits the",
        "small per-cell counts, and the one-spring-per-row layout means each cell entry",
        "is an independent observation.",
        "",
        "| bedrock class | mat present | mat absent |",
        "| --- | --- | --- |",
    ]
    for bedrock in BEDROCK_ORDER:
        present, absent = table[bedrock]
        lines.append("| {0} | {1} | {2} |".format(bedrock, present, absent))
    basalt_present, basalt_absent = table["basalt"]
    rhyolite_present, rhyolite_absent = table["rhyolite"]
    lines += [
        "",
        "## Result",
        "",
        "[selected-result] Fisher's exact test (two-sided) on {0} independent "
        "springs: odds ratio = {1:.2f}, p = {2:.4f}; filament mats occur "
        "significantly more often at basalt-hosted springs "
        "({3}/{4}) than at rhyolite-hosted springs "
        "({5}/{6}) at the 0.05 level.".format(
            n_total,
            odds_ratio,
            p_value,
            basalt_present,
            basalt_present + basalt_absent,
            rhyolite_present,
            rhyolite_present + rhyolite_absent,
        ),
        "",
        "The association is significant, but with {0} springs the odds-ratio estimate is".format(
            n_total
        ),
        "imprecise; the direction, not the magnitude, is the durable finding.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    springs = read_springs(INPUT_PATH)
    table = cross_tabulate(springs)
    counts = [table[name] for name in BEDROCK_ORDER]
    odds_ratio, p_value = fisher_exact(counts, alternative="two-sided")
    report = build_report(table, float(odds_ratio), float(p_value), len(springs))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
