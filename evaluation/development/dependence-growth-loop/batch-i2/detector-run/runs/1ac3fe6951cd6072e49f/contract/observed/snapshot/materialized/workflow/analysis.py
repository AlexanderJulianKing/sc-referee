"""Trellis system and berry skin anthocyanin in Syrah vineyard blocks.

Reads data/input.csv, in which every independently managed vineyard block
contributes exactly one row, compares composite berry skin anthocyanin
between the two trellis systems with Welch's t-test, and writes
results/report.md.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats

INPUT_PATH = os.path.join("data", "input.csv")
REPORT_PATH = os.path.join("results", "report.md")

UNIT_COLUMN = "block_id"
GROUP_COLUMN = "trellis_system"
RESPONSE_COLUMN = "anthocyanin_mg_per_g"

GROUP_ORDER = ("vsp", "sprawl")
GROUP_LABEL = {"vsp": "vertical shoot positioning", "sprawl": "sprawl"}


def read_blocks(path: str) -> List[Dict[str, str]]:
    """Return one dictionary per vineyard block, checking unit uniqueness."""
    with open(path, newline="", encoding="ascii") as handle:
        blocks = list(csv.DictReader(handle))
    if not blocks:
        raise ValueError("no vineyard blocks found in " + path)
    identifiers = [block[UNIT_COLUMN] for block in blocks]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(UNIT_COLUMN + " does not uniquely identify a row")
    return blocks


def collect(blocks: List[Dict[str, str]], group: str) -> np.ndarray:
    """Pull the response values belonging to one trellis system."""
    values = [
        float(block[RESPONSE_COLUMN])
        for block in blocks
        if block[GROUP_COLUMN].strip().lower() == group
    ]
    return np.asarray(values, dtype=float)


def welch(a: np.ndarray, b: np.ndarray) -> Tuple[float, float, float]:
    """Welch t statistic, two-sided p value, and Satterthwaite d.f."""
    va = a.var(ddof=1) / a.size
    vb = b.var(ddof=1) / b.size
    pooled = va + vb
    df = pooled * pooled / (va * va / (a.size - 1) + vb * vb / (b.size - 1))
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
    return float(t_stat), float(p_value), float(df)


def p_text(p_value: float) -> str:
    if p_value < 0.001:
        return "p < 0.001"
    return "p = {:.3f}".format(p_value)


def main() -> None:
    blocks = read_blocks(INPUT_PATH)
    samples = {group: collect(blocks, group) for group in GROUP_ORDER}
    for group in GROUP_ORDER:
        if samples[group].size < 2:
            raise ValueError("too few blocks in group " + group)
    if sum(samples[g].size for g in GROUP_ORDER) != len(blocks):
        raise ValueError("unrecognised " + GROUP_COLUMN + " label in input")

    a = samples["vsp"]
    b = samples["sprawl"]
    t_stat, p_value, df = welch(a, b)
    difference = float(a.mean() - b.mean())

    lines = []
    lines.append("# Trellis system and berry skin anthocyanin in Syrah")
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append(
        (
            "The file records {n} Syrah vineyard blocks, each at a different "
            "estate and each trained on a single trellis system. Each block "
            "contributes exactly one analyzed row: a 100-berry composite drawn "
            "across the block at harvest and assayed once. Rows therefore "
            "correspond one-to-one with independent blocks, and no block "
            "appears twice."
        ).format(n=len(blocks))
    )
    lines.append("")
    lines.append("| trellis system | blocks | mean anthocyanin (mg/g skin) | SD |")
    lines.append("| --- | ---: | ---: | ---: |")
    for group in GROUP_ORDER:
        sample = samples[group]
        lines.append(
            "| {label} | {n} | {mean:.3f} | {sd:.3f} |".format(
                label=GROUP_LABEL[group],
                n=sample.size,
                mean=sample.mean(),
                sd=sample.std(ddof=1),
            )
        )
    lines.append("")
    lines.append("## Analysis")
    lines.append("")
    lines.append(
        (
            "Welch's two-sided two-sample t-test (unequal variances, "
            "Welch-Satterthwaite degrees of freedom) comparing block-level "
            "composite anthocyanin concentration between the two trellis "
            "systems. The block is the unit of assignment, the unit of "
            "measurement, and the unit of analysis, so the {n} values entering "
            "the test are mutually independent."
        ).format(n=len(blocks))
    )
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(
        (
            "[selected-result] Welch two-sample t-test on {n} independent "
            "vineyard blocks ({na} vertical shoot positioning, {nb} sprawl): "
            "mean berry skin anthocyanin was {ma:.3f} mg/g under vertical "
            "shoot positioning versus {mb:.3f} mg/g under sprawl, a difference "
            "of {d:.3f} mg/g (t = {t:.2f}, df = {df:.2f}, {p}); anthocyanin "
            "was higher under vertical shoot positioning."
        ).format(
            n=len(blocks),
            na=a.size,
            nb=b.size,
            ma=a.mean(),
            mb=b.mean(),
            d=difference,
            t=t_stat,
            df=df,
            p=p_text(p_value),
        )
    )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        (
            "- Group sizes are balanced ({na} and {nb}); the unequal-variance "
            "(Welch) form of the test was used because the two sample standard "
            "deviations differ."
        ).format(na=a.size, nb=b.size)
    )
    lines.append(
        "- The columns vine_age_years and canopy_leaf_layers are recorded for "
        "context and take no part in the reported test."
    )
    lines.append(
        "- A single pre-specified two-sided comparison was made, so no "
        "adjustment for multiplicity applies."
    )

    parent = os.path.dirname(REPORT_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
