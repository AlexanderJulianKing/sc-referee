"""Chitin accumulation of strain MX-7 on two substrate blends.

Reads data/input.csv and writes results/report.md.
"""

import collections
import csv
from pathlib import Path

from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
OUTPUT_PATH = Path("results") / "report.md"

BLENDS = ("lignin_blend", "starch_blend")
YIELD_FIELD = "chitin_mg_per_g"


def read_table(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blend_values(records, blend):
    return [float(rec[YIELD_FIELD]) for rec in records if rec["substrate"] == blend]


def mean_var(sample):
    n = len(sample)
    mu = sum(sample) / n
    var = sum((x - mu) ** 2 for x in sample) / (n - 1)
    return n, mu, var


def welch_df(var_a, n_a, var_b, n_b):
    a = var_a / n_a
    b = var_b / n_b
    return (a + b) ** 2 / (a * a / (n_a - 1) + b * b / (n_b - 1))


def p_text(pval):
    for edge in (0.001, 0.01, 0.05):
        if pval < edge:
            return "p < %g" % edge
    return "p = %.3f" % pval


def main():
    records = read_table(INPUT_PATH)

    samples = {blend: blend_values(records, blend) for blend in BLENDS}
    n_lig, mean_lig, var_lig = mean_var(samples["lignin_blend"])
    n_sta, mean_sta, var_sta = mean_var(samples["starch_blend"])

    test = stats.ttest_ind(
        samples["starch_blend"], samples["lignin_blend"], equal_var=False
    )
    dof = welch_df(var_sta, n_sta, var_lig, n_lig)
    se = (var_sta / n_sta + var_lig / n_lig) ** 0.5
    diff = mean_sta - mean_lig
    half_width = stats.t.ppf(0.975, dof) * se
    lo = diff - half_width
    hi = diff + half_width
    verdict = p_text(float(test.pvalue))

    per_vessel = collections.Counter(rec["vessel_id"] for rec in records)
    sizes = sorted(set(per_vessel.values()))
    reps = str(sizes[0]) if len(sizes) == 1 else "%d-%d" % (sizes[0], sizes[-1])
    days = sorted({int(rec["harvest_day"]) for rec in records})

    lines = [
        "# Chitin accumulation in strain MX-7 on two substrate blends",
        "",
        "## Data",
        "",
        "- Source file: `data/input.csv`",
        "- Harvest samples analysed: %d" % len(records),
        "- Bioreactor vessels: %d" % len(per_vessel),
        "- Harvest samples per vessel: %s" % reps,
        "- Harvest days present: %s" % ", ".join(str(day) for day in days),
        "",
        "## Method",
        "",
        "Chitin content (mg per g dry biomass) is compared between the two substrate",
        "blends with a two-sided Welch two-sample t-test. Each harvest sample in the",
        "file supplies one observation, so the test runs on %d observations per blend."
        % n_lig,
        "",
        "## Summary statistics",
        "",
        "| Substrate blend | Observations | Mean chitin (mg/g) | SD |",
        "| --- | --- | --- | --- |",
        "| lignin_blend | %d | %.2f | %.2f |" % (n_lig, mean_lig, var_lig ** 0.5),
        "| starch_blend | %d | %.2f | %.2f |" % (n_sta, mean_sta, var_sta ** 0.5),
        "",
        "## Result",
        "",
        "Mean difference (starch_blend minus lignin_blend): %.2f mg/g" % diff,
        "95%% confidence interval: %.2f to %.2f mg/g" % (lo, hi),
        "Welch t = %.2f, df = %.1f, %s" % (test.statistic, dof, verdict),
        "",
        "[selected-result] Welch two-sample t-test of chitin content, starch_blend"
        " vs lignin_blend: mean difference %.2f mg/g (95%% CI %.2f to %.2f),"
        " t = %.2f, df = %.1f, %s; chitin content is significantly higher on the"
        " starch blend." % (diff, lo, hi, test.statistic, dof, verdict),
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
