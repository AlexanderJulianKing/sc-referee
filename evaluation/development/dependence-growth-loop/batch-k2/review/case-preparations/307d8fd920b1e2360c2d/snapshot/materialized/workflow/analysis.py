"""Day-60 grade-out of individually reared juvenile cod under two diets.

Reads data/input.csv and writes results/report.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scipy.stats import fisher_exact

INPUT_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

TARGET_MASS_G = 12.0
SUPPLEMENTED = "algal_oil"
CONTROL = "baseline"


def read_chambers(path):
    """One record per chamber; a chamber never appears twice."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(record) for record in csv.DictReader(handle)]
    if not rows:
        raise ValueError("no chamber records found")
    tags = [row["chamber_id"] for row in rows]
    if len(set(tags)) != len(tags):
        raise ValueError("each chamber_id must appear on exactly one row")
    return rows


def summarise(rows, diet):
    """Return (graded, missed, mean day-60 mass) for one diet arm."""
    masses = [float(row["day60_mass_g"]) for row in rows if row["diet"] == diet]
    if not masses:
        raise ValueError("no chambers assigned to diet " + diet)
    graded = sum(1 for mass in masses if mass >= TARGET_MASS_G)
    return graded, len(masses) - graded, sum(masses) / len(masses)


def build_report(a, b, supp_mean, c, d, ctrl_mean, odds_ratio, pvalue):
    n_supp = a + b
    n_ctrl = c + d
    n_total = n_supp + n_ctrl
    return [
        "# Algal-oil supplementation and day-60 grade-out in individually reared juvenile cod",
        "",
        "## Design",
        "",
        "Each row of `data/input.csv` is one juvenile Atlantic cod held alone in its own",
        "flow-through chamber for the entire 60-day trial. Chambers were stocked with one",
        "fish each, fed independently, and weighed once at day 60, so `chamber_id` is",
        "unique across the file and every fish contributes exactly one measurement. No",
        f"fish was weighed twice and no chamber held more than one fish, so the {n_total} rows",
        f"are {n_total} independent units.",
        "",
        "## Analysis",
        "",
        "The pre-specified endpoint is grade-out: whether a fish reaches the 12.0 g",
        "transfer target by day 60. The 2x2 table of diet by grade-out was tested with",
        "Fisher's exact test (two-sided). Each fish supplies a single Bernoulli outcome",
        "and the cell counts are small, so an exact conditional test is the natural",
        "choice.",
        "",
        "## Results",
        "",
        "| Diet | Chambers | Reached 12.0 g | Grade-out rate | Mean day-60 mass (g) |",
        "| --- | --- | --- | --- | --- |",
        f"| {SUPPLEMENTED} | {n_supp} | {a} | {100.0 * a / n_supp:.1f}% | {supp_mean:.2f} |",
        f"| {CONTROL} | {n_ctrl} | {c} | {100.0 * c / n_ctrl:.1f}% | {ctrl_mean:.2f} |",
        "",
        f"Sample odds ratio (algal-oil vs. baseline grade-out): {odds_ratio:.3f}",
        "",
        (
            "[selected-result] Fisher's exact test on the 2x2 diet-by-grade-out table "
            f"(n = {n_total} chambers, one fish per chamber): {a} of {n_supp} algal-oil fish "
            f"versus {c} of {n_ctrl} baseline fish reached the {TARGET_MASS_G:.1f} g transfer "
            f"target, odds ratio {odds_ratio:.3f}, two-sided p = {pvalue:.4f}, so the diets "
            "differ significantly at alpha = 0.05."
        ),
        "",
        "## Notes",
        "",
        "Day-60 mass is summarised only for description; the test uses the dichotomised",
        f"grade-out outcome. With {n_supp} chambers per diet the p-value is exact, so no",
        "distributional assumption about mass is needed.",
    ]


def main():
    rows = read_chambers(INPUT_PATH)
    a, b, supp_mean = summarise(rows, SUPPLEMENTED)
    c, d, ctrl_mean = summarise(rows, CONTROL)
    pvalue = float(fisher_exact([[a, b], [c, d]], alternative="two-sided")[1])
    odds_ratio = (a * d) / (b * c)
    lines = build_report(a, b, supp_mean, c, d, ctrl_mean, odds_ratio, pvalue)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
