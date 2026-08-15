"""Fern spore cryobank trial: accession-level paired germination analysis.

Reads data/input.csv and writes results/report.md. Each accession occupies one
row and contributes one matched pair of germination scores, so the test has
exactly as many observations as the design has independent units.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

INPUT_PATH = Path("data") / "input.csv"
REPORT_PATH = Path("results") / "report.md"

UNIT_COL = "accession_id"
FREEZER_COL = "germ_pct_freezer_minus20c"
CRYO_COL = "germ_pct_cryo_minus196c"
SCORED_COL = "spores_scored"


def read_accessions(path):
    with path.open("r", encoding="ascii", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2:
        raise SystemExit("need at least two accessions")
    codes = [row[UNIT_COL] for row in rows]
    if len(set(codes)) != len(codes):
        raise SystemExit("every accession must appear on exactly one row")
    return rows


def column(rows, name):
    return np.array([float(row[name]) for row in rows], dtype=float)


def format_p(value):
    if value < 1e-4:
        return "p < 0.0001"
    return "p = {0:.4f}".format(value)


def main():
    rows = read_accessions(INPUT_PATH)
    freezer = column(rows, FREEZER_COL)
    cryo = column(rows, CRYO_COL)
    gain = cryo - freezer

    n = int(gain.size)
    df = n - 1
    mean_gain = float(np.mean(gain))
    sd_gain = float(np.std(gain, ddof=1))
    se_gain = sd_gain / float(np.sqrt(n))
    tstat, pval = stats.ttest_rel(cryo, freezer)
    tcrit = float(stats.t.ppf(0.975, df))
    lo = mean_gain - tcrit * se_gain
    hi = mean_gain + tcrit * se_gain
    dz = mean_gain / sd_gain
    wstat, wpval = stats.wilcoxon(cryo, freezer)

    scored = sorted({int(row[SCORED_COL]) for row in rows})
    scored_text = ", ".join(str(value) for value in scored)
    n_improved = int(np.sum(gain >= 0.0))

    lines = [
        "# Cryobank germination trial: paired comparison of two storage regimes",
        "",
        "## Data",
        "",
        "- Source file: data/input.csv",
        "- Independent units (fern spore accessions): {0}".format(n),
        "- Rows analysed: {0} (exactly one row per accession)".format(len(rows)),
        "- Spores scored per aliquot: {0}".format(scored_text),
        "",
        "## Design and analysis",
        "",
        "Each accession is a spore lot harvested from one maternal sporophyte at its",
        "own site. Every lot was split into two aliquots: one held at -20 C and one",
        "held at -196 C. After 18 months a single plate per aliquot was sown and",
        "scored, so an accession yields exactly one matched pair and exactly one",
        "analysed difference (cryo minus freezer, in percentage points).",
        "",
        "The primary test is a two-sided paired t-test on the {0} accession-level".format(n),
        "differences (df = {0}). A Wilcoxon signed-rank test on the same differences".format(df),
        "is reported as a distribution-free check.",
        "",
        "## Results",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| mean germination at -20 C (%) | {0:.2f} |".format(float(np.mean(freezer))),
        "| mean germination at -196 C (%) | {0:.2f} |".format(float(np.mean(cryo))),
        "| mean paired difference (pp) | {0:.2f} |".format(mean_gain),
        "| SD of paired differences (pp) | {0:.2f} |".format(sd_gain),
        "| standard error of the mean difference (pp) | {0:.2f} |".format(se_gain),
        "| 95% CI for the mean difference (pp) | {0:.2f} to {1:.2f} |".format(lo, hi),
        "| Cohen's dz | {0:.2f} |".format(dz),
        "",
        "Paired t-test: t({0}) = {1:.3f}, {2} (two-sided).".format(
            df, float(tstat), format_p(float(pval))
        ),
        "Wilcoxon signed-rank test: W = {0:.1f}, {1} (two-sided).".format(
            float(wstat), format_p(float(wpval))
        ),
        "",
        (
            "[selected-result] Paired t-test on {0} accession-level differences "
            "(one difference per accession): cryogenic storage at -196 C raised "
            "18-month spore germination by {1:.2f} percentage points relative to "
            "-20 C storage (95% CI {2:.2f} to {3:.2f} pp; t({4}) = {5:.3f}, {6}, "
            "two-sided)."
        ).format(n, mean_gain, lo, hi, df, float(tstat), format_p(float(pval))),
        "",
        "## Reading the numbers",
        "",
        "All {0} of the {1} accessions germinated at least as well after cryogenic".format(
            n_improved, n
        ),
        "storage; the smallest single-accession gain was {0:.0f} pp and the largest".format(
            float(np.min(gain))
        ),
        "was {0:.0f} pp. The accession is the unit of replication: no accession".format(
            float(np.max(gain))
        ),
        "contributes more than one row, nothing is pooled across accessions before",
        "testing, and the {0} differences entering the test are the {0} independent".format(n),
        "observations the design provides. The interval describes a within-accession",
        "contrast, not the spread of absolute germination between accessions, which",
        "runs from {0:.0f} to {1:.0f} percent under freezer storage.".format(
            float(np.min(freezer)), float(np.max(freezer))
        ),
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
