"""Whole-basin comparison of dissolved organic carbon export in a boreal
peatland restoration survey.

Each surveyed basin drains to its own outlet and is sampled once at the end of
the growing season, so a row of the input table is a single independent
hydrological unit.  With only five basins per treatment the group contrast is
referred to the complete enumeration of basin-to-treatment splits instead of an
asymptotic approximation.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import List, Sequence, Tuple

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COLUMN = "basin_id"
GROUP_COLUMN = "treatment"
RESPONSE_COLUMN = "doc_mg_per_l"
FOCAL_GROUP = "rewetted"
REFERENCE_GROUP = "drained"

# Slack for the ">= observed" comparison so that a split tied with the observed
# contrast stays in the tail instead of being lost to binary rounding.
TIE_SLACK = 1e-9

Basin = Tuple[str, str, float]


@dataclass(frozen=True)
class Outcome:
    n_focal: int
    n_reference: int
    mean_focal: float
    mean_reference: float
    observed: float
    extreme: int
    total: int
    p_value: float

    @property
    def n_total(self) -> int:
        return self.n_focal + self.n_reference


def read_basins(path: Path) -> List[Basin]:
    with path.open(newline="", encoding="ascii") as handle:
        records = list(csv.DictReader(handle))
    basins = [
        (
            row[UNIT_COLUMN].strip(),
            row[GROUP_COLUMN].strip(),
            float(row[RESPONSE_COLUMN]),
        )
        for row in records
    ]
    codes = [basin[0] for basin in basins]
    if len(set(codes)) != len(codes):
        raise ValueError("each basin must occupy exactly one row")
    labels = {basin[1] for basin in basins}
    if labels != {FOCAL_GROUP, REFERENCE_GROUP}:
        raise ValueError("unexpected treatment labels: {0}".format(sorted(labels)))
    return basins


def average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def split_contrast(values: Sequence[float], focal: Sequence[int]) -> float:
    chosen = set(focal)
    inside = [value for position, value in enumerate(values) if position in chosen]
    outside = [value for position, value in enumerate(values) if position not in chosen]
    return average(inside) - average(outside)


def analyse(basins: Sequence[Basin]) -> Outcome:
    values = [basin[2] for basin in basins]
    focal = [i for i, basin in enumerate(basins) if basin[1] == FOCAL_GROUP]
    reference = [i for i, basin in enumerate(basins) if basin[1] == REFERENCE_GROUP]
    observed = split_contrast(values, focal)
    cutoff = abs(observed) - TIE_SLACK

    total = 0
    extreme = 0
    for candidate in combinations(range(len(values)), len(focal)):
        total += 1
        if abs(split_contrast(values, candidate)) >= cutoff:
            extreme += 1

    return Outcome(
        n_focal=len(focal),
        n_reference=len(reference),
        mean_focal=average([values[i] for i in focal]),
        mean_reference=average([values[i] for i in reference]),
        observed=observed,
        extreme=extreme,
        total=total,
        p_value=extreme / total,
    )


def build_report(outcome: Outcome) -> str:
    verdict = (
        "[selected-result] Exact two-sided permutation test over {0} "
        "basin-to-treatment splits: mean DOC is {1:+.2f} mg/L higher in rewetted "
        "basins ({2:.2f} vs {3:.2f} mg/L), p = {4:.4f} ({5}/{0} splits at least "
        "as extreme), which does not reach the 0.05 level."
    ).format(
        outcome.total,
        outcome.observed,
        outcome.mean_focal,
        outcome.mean_reference,
        outcome.p_value,
        outcome.extreme,
    )
    lines = [
        "# Dissolved organic carbon export after peatland rewetting",
        "",
        "## Data",
        "",
        "A boreal restoration survey of hydrologically isolated peat basins. Each",
        "basin contributes exactly one row of the table: a single end-of-season",
        "composite sample drawn at that basin's own outlet and measured once. Half",
        "of the basins were rewetted by ditch blocking, the rest were left drained.",
        "",
        "| group | basins | mean DOC (mg/L) |",
        "| --- | --- | --- |",
        "| {0} | {1} | {2:.2f} |".format(
            FOCAL_GROUP, outcome.n_focal, outcome.mean_focal
        ),
        "| {0} | {1} | {2:.2f} |".format(
            REFERENCE_GROUP, outcome.n_reference, outcome.mean_reference
        ),
        "",
        "## Analysis",
        "",
        "Exact two-sided permutation test on the difference between group mean DOC.",
        "All {0} ways of splitting the {1} basins into a rewetted set of {2} and a".format(
            outcome.total, outcome.n_total, outcome.n_focal
        ),
        "drained set of {0} were enumerated, and the observed contrast was compared".format(
            outcome.n_reference
        ),
        "with the resulting distribution of absolute mean differences. The basin is",
        "both the randomisation unit and the unit of analysis: no basin is entered",
        "more than once, so the permutation reference set is the correct one.",
        "",
        "## Result",
        "",
        "Observed contrast (rewetted minus drained): {0:+.2f} mg/L.".format(
            outcome.observed
        ),
        "Splits at least as extreme as the observed one: {0} of {1}.".format(
            outcome.extreme, outcome.total
        ),
        "",
        verdict,
        "",
        "## Reading",
        "",
        "The point estimate is a substantial rise in DOC export after rewetting, but",
        "with five basins per arm the exact test cannot separate it from assignment",
        "noise: about one split in sixteen reproduces a contrast this large. The",
        "finding is best read as suggestive and underpowered rather than as evidence",
        "of no effect.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    basins = read_basins(INPUT_PATH)
    outcome = analyse(basins)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(build_report(outcome))


if __name__ == "__main__":
    main()
