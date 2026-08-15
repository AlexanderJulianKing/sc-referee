"""Does clay pelleting change seedling emergence when every pot holds one seed?

Reads data/input.csv (one nursery pot per row) and writes results/report.md.
Each pot contributes exactly one binary outcome, so the 2x2 table of seed
treatment by emergence has one independent Bernoulli trial per cell entry.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

ARMS = ("pelleted", "bare")
ALPHA = 0.05


def read_pots(path):
    """Return the pot records exactly as stored, in file order."""
    with path.open("r", newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle))


def check_one_row_per_pot(rows):
    """Every pot, and every maternal plant, may appear at most once."""
    pots = set()
    mothers = set()
    for row in rows:
        pot = row["pot_id"].strip()
        mother = row["maternal_plant_id"].strip()
        if pot in pots:
            raise ValueError("pot %s appears more than once" % pot)
        if mother in mothers:
            raise ValueError("maternal plant %s appears more than once" % mother)
        pots.add(pot)
        mothers.add(mother)


def cross_tabulate(rows):
    counts = {arm: {"emerged": 0, "not_emerged": 0} for arm in ARMS}
    for row in rows:
        arm = row["seed_treatment"].strip()
        if arm not in counts:
            raise ValueError("unexpected seed_treatment: %s" % arm)
        flag = int(row["emerged_by_day28"])
        if flag not in (0, 1):
            raise ValueError("emerged_by_day28 must be 0 or 1")
        counts[arm]["emerged" if flag == 1 else "not_emerged"] += 1
    return counts


def build_report(rows):
    counts = cross_tabulate(rows)
    table = [[counts[arm]["emerged"], counts[arm]["not_emerged"]] for arm in ARMS]
    (a, b), (c, d) = table
    if min(a + b, c + d) == 0 or b == 0 or c == 0:
        raise ValueError("both arms need emerged and non-emerged pots")

    pvalue = float(fisher_exact(table)[1])
    odds_ratio = (a * d) / (b * c)
    pct_pelleted = 100.0 * a / (a + b)
    pct_bare = 100.0 * c / (c + d)
    gap = pct_pelleted - pct_bare
    significance = "is" if pvalue < ALPHA else "is not"
    n = len(rows)

    lines = [
        "# Pelleted vs. bare seed: emergence in single-seed pots",
        "",
        "## Data",
        "",
        "%d pots, one seed and one maternal plant per pot, each pot scored once for" % n,
        "seedling emergence at day 28. Each pot is an independent experimental unit and",
        "contributes exactly one row.",
        "",
        "| Seed treatment | Emerged | Not emerged | Pots | Emergence |",
        "| --- | --- | --- | --- | --- |",
        "| pelleted | %d | %d | %d | %.1f%% |" % (a, b, a + b, pct_pelleted),
        "| bare | %d | %d | %d | %.1f%% |" % (c, d, c + d, pct_bare),
        "",
        "## Analysis",
        "",
        "Fisher's exact test (two-sided) on the 2x2 table of seed treatment by",
        "emergence at day 28, with one Bernoulli outcome per independent pot.",
        "",
        "## Result",
        "",
        "Sample odds ratio (pelleted vs. bare) = %.2f, two-sided p = %.4f."
        % (odds_ratio, pvalue),
        "Emergence was %.1f percentage points higher in pelleted pots." % gap,
        "",
        "[selected-result] Two-sided Fisher's exact test on %d independent single-seed "
        "pots: emergence %d/%d (%.1f%%) with pelleted seed vs. %d/%d (%.1f%%) with bare "
        "seed, sample odds ratio %.2f, p = %.4f; the difference %s statistically "
        "significant at alpha = %.2f."
        % (
            n,
            a,
            a + b,
            pct_pelleted,
            c,
            c + d,
            pct_bare,
            odds_ratio,
            pvalue,
            significance,
            ALPHA,
        ),
    ]
    return "\n".join(lines) + "\n"


def main():
    rows = read_pots(INPUT_PATH)
    if not rows:
        raise ValueError("no pot records found")
    check_one_row_per_pot(rows)
    report = build_report(rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
