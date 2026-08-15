"""Nest-cavity choice assay for field-collected Temnothorax colonies.

Reads data/input.csv and writes results/report.md.  Every colony was run through
the arena exactly once, so each analysed row is a separate independent unit and
an exact binomial test on the row counts is the right tool.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from scipy.stats import binomtest

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_COLUMN = "colony_id"
GROUP_COLUMN = "source_woodlot"
CHOICE_COLUMN = "chosen_cavity"

PREFERRED = "narrow"
ALTERNATE = "wide"
NULL_P = 0.5
ALPHA = 0.05


def read_assay(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(record) for record in csv.DictReader(handle)]


def check_one_row_per_colony(rows):
    """Confirm the file holds a single assayed row per colony."""
    per_colony = Counter(row[UNIT_COLUMN] for row in rows)
    worst = max(per_colony.values())
    if worst != 1:
        repeated = sorted(cid for cid, k in per_colony.items() if k > 1)
        raise SystemExit(
            "expected one assayed row per colony; repeated: " + ", ".join(repeated)
        )
    return len(per_colony), worst


def tally_by_woodlot(rows, choices):
    tallies = {}
    for row, choice in zip(rows, choices):
        woodlot = row[GROUP_COLUMN]
        if woodlot not in tallies:
            tallies[woodlot] = Counter()
        tallies[woodlot][choice] += 1
    return tallies


def main():
    rows = read_assay(INPUT_PATH)
    if not rows:
        raise SystemExit("data/input.csv contains no data rows")

    n_rows = len(rows)
    n_colonies, max_rows_per_colony = check_one_row_per_colony(rows)

    choices = [row[CHOICE_COLUMN].strip() for row in rows]
    strange = sorted(set(choices) - {PREFERRED, ALTERNATE})
    if strange:
        raise SystemExit("unrecognised cavity labels: " + ", ".join(strange))

    successes = choices.count(PREFERRED)
    result = binomtest(successes, n_rows, NULL_P, alternative="two-sided")
    proportion = successes / n_rows

    by_woodlot = tally_by_woodlot(rows, choices)

    prop_txt = "%.4f" % proportion
    p_txt = "%.6f" % result.pvalue
    verdict = "rejected" if result.pvalue < ALPHA else "not rejected"

    selected = (
        "[selected-result] Exact two-sided binomial test: %d of %d colonies chose the "
        "narrow cavity (proportion %s), p = %s against the no-preference null of %g; "
        "at alpha = %g the null of no cavity preference is %s."
        % (successes, n_rows, prop_txt, p_txt, NULL_P, ALPHA, verdict)
    )

    out = []
    out.append("# Nest-cavity choice in Temnothorax colonies")
    out.append("")
    out.append("## Design")
    out.append("")
    out.append("Each field-collected colony was offered a single two-way choice between a")
    out.append("narrow-entrance cavity and a wide-entrance cavity. A colony was assayed once")
    out.append("and contributes exactly one row, so the rows entering the test are mutually")
    out.append("independent; no colony is counted twice.")
    out.append("")
    out.append("- Rows analysed: %d" % n_rows)
    out.append("- Distinct colonies (colony_id): %d" % n_colonies)
    out.append("- Maximum rows contributed by any one colony: %d" % max_rows_per_colony)
    out.append("")
    out.append("## Analysis")
    out.append("")
    out.append("Exact two-sided binomial test (scipy.stats.binomtest) on the number of")
    out.append(
        "colonies choosing the narrow cavity, against a no-preference null of p = %g."
        % NULL_P
    )
    out.append("")
    out.append("- Colonies choosing narrow: %d of %d" % (successes, n_rows))
    out.append("- Observed proportion choosing narrow: %s" % prop_txt)
    out.append("- Exact two-sided p-value: %s" % p_txt)
    out.append("")
    out.append(selected)
    out.append("")
    out.append("## Choice by source woodlot (descriptive only)")
    out.append("")
    out.append("| source woodlot | narrow | wide | colonies | proportion narrow |")
    out.append("| --- | --- | --- | --- | --- |")
    for woodlot in sorted(by_woodlot):
        tally = by_woodlot[woodlot]
        n_narrow = tally[PREFERRED]
        n_wide = tally[ALTERNATE]
        n_here = n_narrow + n_wide
        out.append(
            "| %s | %d | %d | %d | %.3f |"
            % (woodlot, n_narrow, n_wide, n_here, n_narrow / n_here)
        )
    out.append("")
    out.append("Woodlot tallies are descriptive; they are not tested. The single test above")
    out.append("uses one observation per colony, which is the independent unit of this study.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
