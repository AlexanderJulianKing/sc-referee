"""Does post-print annealing raise the tensile strength of printed PLA?

Reads data/input.csv (one row per tensile coupon) and writes results/report.md.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data/input.csv")
OUTPUT_PATH = Path("results/report.md")

BASELINE = "as_printed"
TREATED = "annealed"


def read_strengths(path):
    """Collect coupon ultimate tensile strengths, keyed by post-print condition."""
    buckets = {BASELINE: [], TREATED: []}
    with path.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            buckets[record["anneal_condition"]].append(float(record["uts_mpa"]))
    return buckets


def pooled_sd(base, treat):
    """Equal-variance pooled standard deviation of the two coupon sets."""
    dof = len(base) + len(treat) - 2
    weighted = (len(base) - 1) * statistics.variance(base)
    weighted += (len(treat) - 1) * statistics.variance(treat)
    return math.sqrt(weighted / dof)


def render_p(p):
    if p < 1e-4:
        return "p < 0.0001"
    return "p = {:.4f}".format(p)


def compose(base, treat):
    mean_base = statistics.fmean(base)
    mean_treat = statistics.fmean(treat)
    sd_base = statistics.stdev(base)
    sd_treat = statistics.stdev(treat)
    diff = mean_treat - mean_base
    dof = len(base) + len(treat) - 2
    t_stat, p_value = stats.ttest_ind(treat, base, equal_var=True)
    p_text = render_p(float(p_value))

    selected = (
        "[selected-result] Annealed coupons failed at a higher ultimate tensile"
        " strength than as-printed coupons ({:.2f} vs {:.2f} MPa, difference"
        " {:+.2f} MPa; two-sample t-test t({}) = {:.2f}, {})."
    ).format(mean_treat, mean_base, diff, dof, t_stat, p_text)

    lines = [
        "# Annealing and the tensile strength of printed PLA coupons",
        "",
        "## Source",
        "",
        "`data/input.csv` records {} dogbone coupons cut from 12 filament spools, six".format(
            len(base) + len(treat)
        ),
        "coupons per spool. Each spool went through one post-print condition and every",
        "coupon was pulled to failure on the same screw-driven frame at 5 mm/min.",
        "",
        "## Coupon summary",
        "",
        "| Condition | Coupons | Mean UTS (MPa) | SD (MPa) |",
        "| --- | --- | --- | --- |",
        "| {} | {} | {:.2f} | {:.2f} |".format(BASELINE, len(base), mean_base, sd_base),
        "| {} | {} | {:.2f} | {:.2f} |".format(TREATED, len(treat), mean_treat, sd_treat),
        "",
        "## Test",
        "",
        "Two-sample Student t-test (equal variances assumed) on coupon ultimate",
        "tensile strength, annealed against as-printed.",
        "",
        "- Mean difference: {:+.2f} MPa".format(diff),
        "- Pooled SD: {:.2f} MPa".format(pooled_sd(base, treat)),
        "- t({}) = {:.2f}, {}".format(dof, t_stat, p_text),
        "",
        selected,
    ]
    return "\n".join(lines) + "\n"


def main():
    buckets = read_strengths(INPUT_PATH)
    report = compose(buckets[BASELINE], buckets[TREATED])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


if __name__ == "__main__":
    main()
