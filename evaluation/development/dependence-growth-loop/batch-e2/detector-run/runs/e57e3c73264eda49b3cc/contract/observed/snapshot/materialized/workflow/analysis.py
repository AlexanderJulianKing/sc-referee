"""Extent change of seagrass meadows under two anchoring regimes.

One CSV row is one surveyed meadow: each meadow contributes a single
extent-change value, so the observations entering the comparison are
independent of one another.
"""

import csv
from pathlib import Path
from statistics import median

from scipy.stats import mannwhitneyu

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

UNIT_COLUMN = "meadow_id"
REGIME_COLUMN = "anchoring_regime"
RESPONSE_COLUMN = "area_change_pct_2015_2025"
PROTECTED = "no_anchor_zone"
OPEN_ACCESS = "open_access"


def read_meadows(path):
    """Return the survey records, expecting one record per meadow."""
    with path.open(newline="", encoding="ascii") as handle:
        records = list(csv.DictReader(handle))
    labels = [record[UNIT_COLUMN] for record in records]
    if not labels:
        raise ValueError("no survey records found")
    if len(set(labels)) != len(labels):
        raise ValueError("every meadow must appear on exactly one row")
    return records


def split_by_regime(records):
    """Split the decadal area changes into the two anchoring regimes."""
    grouped = {PROTECTED: [], OPEN_ACCESS: []}
    for record in records:
        regime = record[REGIME_COLUMN]
        if regime not in grouped:
            raise ValueError("unexpected anchoring regime: " + regime)
        grouped[regime].append(float(record[RESPONSE_COLUMN]))
    return grouped[PROTECTED], grouped[OPEN_ACCESS]


def compose_report(protected, open_access):
    """Run the rank test on the meadow-level values and render the report."""
    outcome = mannwhitneyu(
        protected,
        open_access,
        alternative="two-sided",
        method="exact",
    )
    u_stat = float(outcome.statistic)
    p_value = float(outcome.pvalue)
    rank_biserial = 2.0 * u_stat / (len(protected) * len(open_access)) - 1.0
    med_protected = median(protected)
    med_open = median(open_access)

    lines = [
        "# Seagrass meadow extent change under two anchoring regimes",
        "",
        "## Data",
        "",
        "Each row of `data/input.csv` is one seagrass meadow surveyed once, so the",
        "meadow is the independent unit and contributes exactly one extent-change value.",
        "",
        f"- Meadows analysed: {len(protected) + len(open_access)}",
        f"- No-anchoring zones: {len(protected)} (median extent change {med_protected:.2f} %)",
        f"- Open-access meadows: {len(open_access)} (median extent change {med_open:.2f} %)",
        "",
        "## Analysis",
        "",
        "Two-sided Mann-Whitney U test comparing the 2015-2025 change in mapped meadow",
        "area between no-anchoring zones and open-access meadows. The exact null",
        f"distribution is used ({len(protected)} and {len(open_access)} meadows per regime, all values distinct), so",
        "no normal approximation or tie correction enters the calculation.",
        "",
        "## Result",
        "",
        f"- U statistic (no-anchoring zones) = {u_stat:.1f}",
        f"- Exact two-sided p-value = {p_value:.4f}",
        f"- Rank-biserial correlation = {rank_biserial:.3f}",
        "",
        (
            "[selected-result] Meadow extent change differed between anchoring regimes "
            f"(exact two-sided Mann-Whitney U = {u_stat:.1f}, "
            f"{len(protected)} vs {len(open_access)} meadows, p = {p_value:.4f}, "
            f"rank-biserial {rank_biserial:.3f}): no-anchoring meadows gained area "
            f"(median +{med_protected:.2f} %) while open-access meadows lost area "
            f"(median {med_open:.2f} %)."
        ),
    ]
    return "\n".join(lines) + "\n"


def main():
    records = read_meadows(INPUT_PATH)
    protected, open_access = split_by_regime(records)
    report = compose_report(protected, open_access)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
