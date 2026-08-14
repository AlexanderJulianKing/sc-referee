"""Bench-scale anaerobic digestion trial.

Reads the cycle-level methane yields in data/input.csv, collapses every
digester to a single mean, and writes the digester-level comparison to
results/report.md.
"""

import csv
import statistics
from itertools import combinations
from math import sqrt
from pathlib import Path

INPUT_FILE = Path("data/input.csv")
OUTPUT_FILE = Path("results/report.md")

UNIT_COL = "digester_id"
GROUP_COL = "pretreatment"
CYCLE_COL = "feed_cycle"
YIELD_COL = "ch4_yield_ml_per_g_vs"

CONTROL = "untreated"
TREATED = "steam_exploded"
CYCLES_PER_DIGESTER = 4
TOL = 1e-9


def read_cycles(path):
    """Return unit order, unit -> label, unit -> [(cycle, yield)] and the row count."""
    order = []
    group_of = {}
    cycles_of = {}
    n_rows = 0
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            n_rows += 1
            unit = row[UNIT_COL]
            label = row[GROUP_COL]
            if unit not in cycles_of:
                order.append(unit)
                group_of[unit] = label
                cycles_of[unit] = []
            elif group_of[unit] != label:
                raise ValueError("digester " + unit + " carries two pretreatment labels")
            cycles_of[unit].append((int(row[CYCLE_COL]), float(row[YIELD_COL])))
    return order, group_of, cycles_of, n_rows


def collapse(order, cycles_of):
    """One mean specific methane yield per digester, i.e. per independent unit."""
    means = []
    for unit in order:
        records = sorted(cycles_of[unit])
        if len(records) != CYCLES_PER_DIGESTER:
            raise ValueError("digester " + unit + " does not have the expected cycles")
        means.append(statistics.mean(value for _, value in records))
    return means


def split_gap(values, picked):
    inside = set(picked)
    left = [v for i, v in enumerate(values) if i in inside]
    right = [v for i, v in enumerate(values) if i not in inside]
    return abs(statistics.mean(left) - statistics.mean(right))


def exact_permutation(values, treated_idx):
    observed = split_gap(values, treated_idx)
    total = 0
    extreme = 0
    for combo in combinations(range(len(values)), len(treated_idx)):
        total += 1
        if split_gap(values, combo) >= observed - TOL:
            extreme += 1
    return extreme, total, extreme / total


def pooled_sd(a, b):
    num = (len(a) - 1) * statistics.variance(a) + (len(b) - 1) * statistics.variance(b)
    return sqrt(num / (len(a) + len(b) - 2))


def main():
    order, group_of, cycles_of, n_rows = read_cycles(INPUT_FILE)
    means = collapse(order, cycles_of)
    labels = [group_of[unit] for unit in order]
    if set(labels) != {CONTROL, TREATED}:
        raise ValueError("unexpected pretreatment labels")

    control = [m for m, lab in zip(means, labels) if lab == CONTROL]
    treated = [m for m, lab in zip(means, labels) if lab == TREATED]
    treated_idx = [i for i, lab in enumerate(labels) if lab == TREATED]

    control_mean = statistics.mean(control)
    treated_mean = statistics.mean(treated)
    difference = treated_mean - control_mean
    effect = difference / pooled_sd(control, treated)
    extreme, total, p_value = exact_permutation(means, treated_idx)
    n_units = len(order)

    lines = [
        "# Steam-explosion pretreatment and specific methane yield",
        "",
        "## Data",
        "",
        "%d feeding-cycle measurements from %d bench-scale mesophilic digesters, %d"
        % (n_rows, n_units, CYCLES_PER_DIGESTER),
        "consecutive cycles per digester. Feedstock pretreatment (untreated or",
        "steam_exploded) was assigned to whole digesters, so the digester is the",
        "independent unit and the four cycle yields from one vessel are repeated",
        "measurements of that unit.",
        "",
        "## Analysis",
        "",
        "Each digester was first collapsed to its mean specific methane yield across",
        "its %d cycles, giving one analysed value per independent unit (n = %d). The"
        % (CYCLES_PER_DIGESTER, n_units),
        "two pretreatment groups were then compared with an exact two-sided",
        "permutation test on the difference in group means, enumerating all %d ways"
        % total,
        "of splitting the %d digester means into groups of %d and %d."
        % (n_units, len(treated), len(control)),
        "",
        "## Digester means",
        "",
        "| digester | pretreatment | cycles | mean yield (mL CH4 / g VS) |",
        "| --- | --- | --- | --- |",
    ]
    for unit, label, value in zip(order, labels, means):
        lines.append(
            "| %s | %s | %d | %.2f |" % (unit, label, len(cycles_of[unit]), value)
        )
    lines.extend([
        "",
        "## Group comparison",
        "",
        "| pretreatment | digesters | mean of digester means | SD |",
        "| --- | --- | --- | --- |",
        "| %s | %d | %.2f | %.3f |"
        % (CONTROL, len(control), control_mean, statistics.stdev(control)),
        "| %s | %d | %.2f | %.3f |"
        % (TREATED, len(treated), treated_mean, statistics.stdev(treated)),
        "",
        "Difference (%s - %s): %.2f mL CH4 / g VS." % (TREATED, CONTROL, difference),
        "Cohen's d on digester means: %.2f." % effect,
        "Exact permutation p-value: %.4f (%d of %d splits at least as extreme as"
        % (p_value, extreme, total),
        "the observed difference).",
        "",
        "[selected-result] Steam-explosion pretreatment increased specific methane "
        "yield by %.2f mL CH4 / g VS (%.2f vs %.2f), tested on %d independent "
        "digesters (%d vs %d) with one mean per digester: exact permutation "
        "p = %.4f."
        % (
            difference,
            treated_mean,
            control_mean,
            n_units,
            len(treated),
            len(control),
            p_value,
        ),
        "",
        "## Note on units",
        "",
        "The %d rows in the input file are not %d independent observations. All"
        % (n_rows, n_rows),
        "inference above is based on the %d digester-level means." % n_units,
    ])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
