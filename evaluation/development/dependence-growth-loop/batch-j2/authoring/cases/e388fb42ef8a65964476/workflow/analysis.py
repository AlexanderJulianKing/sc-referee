"""Foredune restoration monitoring: cover-class composition test.

Reads data/input.csv (one surveyed restoration site per row) and writes
results/report.md.  Each site was visited once and carries a single cover-class
label, so the class tally is a tally over independent sites.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

CLASS_ORDER = ("sparse", "patchy", "closed")
REFERENCE_SHARE = {"sparse": 0.60, "patchy": 0.30, "closed": 0.10}
ALPHA = 0.05


def read_sites(path: Path) -> List[Dict[str, str]]:
    """Return the survey rows, checking that every site appears exactly once."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(record) for record in csv.DictReader(handle)]
    if not rows:
        raise ValueError("no survey rows found")
    seen = set()
    for row in rows:
        site = row["site_id"].strip()
        if not site:
            raise ValueError("blank site_id")
        if site in seen:
            raise ValueError("site_id appears more than once: {0}".format(site))
        seen.add(site)
        label = row["cover_class"].strip()
        if label not in CLASS_ORDER:
            raise ValueError("unexpected cover_class: {0}".format(label))
    return rows


def tally_classes(rows: List[Dict[str, str]]) -> np.ndarray:
    """Count sites per cover class, in the fixed reporting order."""
    counts = Counter(row["cover_class"].strip() for row in rows)
    return np.array([counts[name] for name in CLASS_ORDER], dtype=float)


def build_report(observed, expected, contributions, statistic, pvalue, effect):
    """Render the markdown report as one string."""
    n = int(round(float(observed.sum())))
    verdict = "reject" if pvalue < ALPHA else "do not reject"
    outcome = "differs from" if pvalue < ALPHA else "is compatible with"

    lines = []
    lines.append(
        "# Cover-class composition of restored foredunes, 2024 shoreline survey"
    )
    lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append("- Source file: `data/input.csv`")
    lines.append(
        "- Independent units: {0} restoration sites, one row per site "
        "(site identifiers verified unique).".format(n)
    )
    lines.append(
        "- Response: `cover_class`, one end-of-season classification per site."
    )
    lines.append("")
    lines.append("## Observed versus reference composition")
    lines.append("")
    lines.append(
        "| Cover class | Sites | Observed share | Reference share | "
        "Expected sites | Chi-square contribution |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for idx, name in enumerate(CLASS_ORDER):
        lines.append(
            "| {0} | {1} | {2:.3f} | {3:.2f} | {4:.1f} | {5:.4f} |".format(
                name,
                int(observed[idx]),
                observed[idx] / n,
                REFERENCE_SHARE[name],
                expected[idx],
                contributions[idx],
            )
        )
    lines.append("")
    lines.append("## Test")
    lines.append("")
    lines.append(
        "Pearson chi-square goodness-of-fit test of the {0} site classifications "
        "against the 2019 regional reference composition.".format(n)
    )
    lines.append("")
    lines.append("- Chi-square statistic: {0:.4f}".format(statistic))
    lines.append("- Degrees of freedom: {0}".format(len(CLASS_ORDER) - 1))
    lines.append("- p-value: {0:.6f}".format(pvalue))
    lines.append("- Effect size (Cohen's w): {0:.4f}".format(effect))
    lines.append(
        "- Decision at alpha = {0:.2f}: {1} the reference composition.".format(
            ALPHA, verdict
        )
    )
    lines.append("")
    lines.append(
        "[selected-result] Chi-square goodness-of-fit on {0} independent restoration "
        "sites (one classification per site): chi-square(2) = {1:.4f}, p = {2:.6f}, "
        "Cohen's w = {3:.4f}; the 2024 cover-class composition ({4} sparse / "
        "{5} patchy / {6} closed) {7} the 2019 reference composition of "
        "0.60 / 0.30 / 0.10 at alpha = 0.05.".format(
            n,
            statistic,
            pvalue,
            effect,
            int(observed[0]),
            int(observed[1]),
            int(observed[2]),
            outcome,
        )
    )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "Every site contributes exactly one classification, so the tallied counts are "
        "{0} independent observations. The columns `shore_marker_km`, "
        "`foredune_width_m` and `sand_ph` describe the sites and were not used by "
        "this test.".format(n)
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = read_sites(INPUT_PATH)
    observed = tally_classes(rows)
    n = float(observed.sum())
    expected = np.array([REFERENCE_SHARE[name] * n for name in CLASS_ORDER])
    result = stats.chisquare(f_obs=observed, f_exp=expected)
    statistic = float(result.statistic)
    pvalue = float(result.pvalue)
    contributions = (observed - expected) ** 2 / expected
    effect = float(np.sqrt(statistic / n))
    report = build_report(
        observed, expected, contributions, statistic, pvalue, effect
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
