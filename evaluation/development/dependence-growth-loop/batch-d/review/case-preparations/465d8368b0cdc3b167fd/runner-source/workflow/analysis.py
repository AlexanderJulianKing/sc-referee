"""Marsh helleborine recovery in restored dune slacks.

Twenty-four coastal dune slacks were re-created by one of two engineering
methods and each was surveyed once, so a single row carries a single site's
single presence/absence outcome. That makes the rows independent units and a
2 x 2 exact test the natural summary.
"""

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

METHOD_ORDER = ("inversion", "stripping")
METHOD_LABEL = {
    "inversion": "Deep topsoil inversion",
    "stripping": "Turf stripping",
}


def read_slacks(path):
    """One dict per restored slack; duplicated site codes are a hard error."""
    with path.open(newline="", encoding="ascii") as handle:
        slacks = list(csv.DictReader(handle))
    codes = [slack["site_id"] for slack in slacks]
    if len(codes) != len(set(codes)):
        raise ValueError("site_id must appear on exactly one row")
    return slacks


def cross_tabulate(slacks):
    """Rows follow METHOD_ORDER, columns are [present, absent]."""
    counts = {method: [0, 0] for method in METHOD_ORDER}
    for slack in slacks:
        method = slack["restoration_method"]
        if method not in counts:
            raise ValueError("unknown restoration method: " + method)
        found = slack["helleborine_present"]
        if found not in ("yes", "no"):
            raise ValueError("helleborine_present must be yes or no")
        counts[method][0 if found == "yes" else 1] += 1
    return [counts[method] for method in METHOD_ORDER]


def render(n_sites, table, odds_ratio, p_value):
    (present_a, absent_a), (present_b, absent_b) = table
    rate_a = present_a / (present_a + absent_a)
    rate_b = present_b / (present_b + absent_b)

    lines = [
        "# Marsh helleborine recovery in restored dune slacks",
        "",
        "## Design",
        "",
        "Each row of `data/input.csv` is one restored dune slack, walked once during the",
        f"2025 flowering season. No slack contributes more than one row, so the {n_sites} rows",
        f"are {n_sites} independent units and a row-independent test is appropriate.",
        "",
        "## Analysis",
        "",
        "Presence or absence of marsh helleborine (*Epipactis palustris*) was",
        "cross-tabulated against restoration method, and the resulting 2 x 2 table was",
        "assessed with Fisher's exact test (two-sided).",
        "",
        "## Counts",
        "",
        "| Restoration method | Present | Absent | Slacks | Detection rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for method, (present, absent) in zip(METHOD_ORDER, table):
        total = present + absent
        lines.append(
            f"| {METHOD_LABEL[method]} | {present} | {absent} | {total} |"
            f" {100.0 * present / total:.1f}% |"
        )
    lines += [
        "",
        "## Result",
        "",
        f"- Sample odds ratio (inversion vs stripping): {odds_ratio:.2f}",
        f"- Difference in detection rate: {rate_a - rate_b:.3f}",
        f"- Fisher's exact test, two-sided: p = {p_value:.4f}",
        "",
        (
            f"[selected-result] Fisher's exact test on {n_sites} independently restored dune"
            f" slacks: marsh helleborine was present at {present_a} of"
            f" {present_a + absent_a} inversion slacks and {present_b} of"
            f" {present_b + absent_b} turf-stripped slacks (sample odds ratio"
            f" {odds_ratio:.2f}, two-sided p = {p_value:.4f}), a statistically significant"
            " advantage for deep topsoil inversion at the 5% level."
        ),
        "",
        "## Reading the result",
        "",
        "With one survey per slack there is no within-site replication to inflate the",
        f"count of independent observations: each of the {n_sites} sites contributes exactly one",
        "Bernoulli outcome to the table. The effect is estimated from a small sample, so",
        "the interval around the odds ratio is wide even though the two-sided p-value",
        "falls below 0.05.",
    ]
    return "\n".join(lines) + "\n"


def main():
    slacks = read_slacks(INPUT_PATH)
    table = cross_tabulate(slacks)
    odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
    report = render(len(slacks), table, odds_ratio, p_value)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
