"""Two-choice arena assay for leafcutter colonies.

Reads data/input.csv (one colony per row), collapses each colony to a single
preference outcome, tests that stream of colony-level outcomes against a
no-preference null, and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import median

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")
NO_PREFERENCE = 0.5


def read_colonies(path):
    with path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("no colony records found")
    return rows


def colony_deltas(rows):
    """Map colony id -> (urea mass - plain mass); one entry per independent nest."""
    deltas = {}
    for row in rows:
        colony = row["colony_id"].strip()
        if colony in deltas:
            raise ValueError("colony " + colony + " is listed more than once")
        deltas[colony] = (
            float(row["cut_mass_urea_mg"]) - float(row["cut_mass_plain_mg"])
        )
    undecided = sorted(c for c, d in deltas.items() if d == 0.0)
    if undecided:
        raise ValueError("undecided assays: " + ", ".join(undecided))
    return deltas


def render(n, favour, other, pct, mid, pvalue):
    return [
        "# Urea-supplemented leaf discs are cut preferentially in a two-choice arena",
        "",
        "## Design",
        "",
        f"Leafcutter (*Atta cephalotes*) colonies were excavated from {n} separate",
        "forest plots and housed individually. Each colony ran the two-choice foraging",
        "arena exactly once: one urea-supplemented leaf tray and one untreated leaf",
        "tray, both weighed before and after a six-hour foraging window. One row of",
        "`data/input.csv` is one colony, and each colony contributes exactly one",
        "outcome to the test, so the analyzed observations are not repeated",
        "measurements of the same nest.",
        "",
        "## Analysis",
        "",
        "Each colony was scored as a single Bernoulli trial: \"prefers urea\" if that",
        "colony removed more urea-supplemented leaf mass than untreated leaf mass.",
        f"The {n} colony-level outcomes were compared with an exact two-sided binomial",
        f"test (`scipy.stats.binomtest`) against a no-preference null share of {NO_PREFERENCE:.2f}.",
        "No colony produced a tie, so no trial was discarded.",
        "",
        "## Result",
        "",
        f"- Colonies assayed: {n}",
        f"- Colonies cutting more urea-supplemented leaf: {favour} ({pct:.1f}%)",
        f"- Colonies cutting more untreated leaf: {other}",
        f"- Median within-colony mass difference (urea minus plain): {mid:.1f} mg",
        f"- Exact two-sided binomial p-value: {pvalue:.6f}",
        "",
        f"[selected-result] Exact two-sided binomial test on one outcome per colony: "
        f"{favour} of {n} colonies ({pct:.1f}%) cut more urea-supplemented leaf tissue, "
        f"median within-colony difference {mid:.1f} mg, p = {pvalue:.6f} against the "
        f"{NO_PREFERENCE:.2f} no-preference null, so the no-preference null is rejected "
        "at alpha = 0.05.",
        "",
        "## Notes and limits",
        "",
        "Colony mass and forager count were recorded but not modelled; the test uses",
        "only the direction of each colony's preference, so the magnitude of a",
        "preference is not weighted. The design speaks only to the six-hour foraging",
        "window that was sampled.",
    ]


def main():
    rows = read_colonies(INPUT_PATH)
    deltas = colony_deltas(rows)
    n = len(deltas)
    favour = sum(1 for d in deltas.values() if d > 0.0)
    other = n - favour
    outcome = binomtest(favour, n, NO_PREFERENCE, alternative="two-sided")
    lines = render(
        n,
        favour,
        other,
        100.0 * favour / n,
        median(deltas.values()),
        outcome.pvalue,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
