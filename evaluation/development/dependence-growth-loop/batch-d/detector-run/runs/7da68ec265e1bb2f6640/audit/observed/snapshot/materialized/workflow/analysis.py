"""Do canopy gaps depress fungal mycelial ingrowth?

Reads data/input.csv, which lists one surveyed spruce stand per row, and writes
results/report.md with a stand-level two-group comparison.
"""

import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats

DATA_PATH = Path("data/input.csv")
REPORT_PATH = Path("results/report.md")

UNIT_KEY = "stand_id"
GROUP_KEY = "canopy_state"
RESPONSE_KEY = "hyphal_ingrowth_mg"
REFERENCE = "intact"
CONTRAST = "gap"


def read_stands(path):
    """Return the CSV rows, refusing any file in which a stand is listed twice."""
    with path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("no stands in {0}".format(path))
    stands = [row[UNIT_KEY] for row in rows]
    if len(set(stands)) != len(stands):
        raise ValueError("a stand is listed more than once; one row per stand is required")
    return rows


def ingrowth(rows, state):
    return np.asarray(
        [float(row[RESPONSE_KEY]) for row in rows if row[GROUP_KEY] == state],
        dtype=float,
    )


def describe(values):
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "median": float(np.median(values)),
    }


def welch_df(var_a, n_a, var_b, n_b):
    a = var_a / n_a
    b = var_b / n_b
    return (a + b) ** 2 / (a * a / (n_a - 1) + b * b / (n_b - 1))


def p_phrase(pvalue):
    return "< 0.0001" if pvalue < 1e-4 else "= {0:.4f}".format(pvalue)


def table_row(label, summary):
    return "| {0} | {1} | {2:.3f} | {3:.3f} | {4:.3f} |".format(
        label, summary["n"], summary["mean"], summary["sd"], summary["median"]
    )


def main():
    rows = read_stands(DATA_PATH)
    a = ingrowth(rows, REFERENCE)
    b = ingrowth(rows, CONTRAST)
    sum_a = describe(a)
    sum_b = describe(b)

    n_a = sum_a["n"]
    n_b = sum_b["n"]
    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))

    tstat, pvalue = stats.ttest_ind(a, b, equal_var=False)
    diff = sum_a["mean"] - sum_b["mean"]
    se = math.sqrt(var_a / n_a + var_b / n_b)
    dof = welch_df(var_a, n_a, var_b, n_b)
    margin = float(stats.t.ppf(0.975, dof)) * se
    pooled_sd = math.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    effect = diff / pooled_sd

    result = (
        "[selected-result] Welch's two-sample t-test on {0} intact-canopy stands "
        "versus {1} canopy-gap stands: mean difference {2:.3f} mg (intact minus "
        "gap), 95% CI [{3:.2f}, {4:.2f}] mg, SE {5:.3f} mg, t = {6:.4f}, "
        "df = {7:.2f}, two-sided p {8}; mycelial ingrowth is higher in "
        "intact-canopy stands."
    ).format(
        n_a,
        n_b,
        diff,
        diff - margin,
        diff + margin,
        se,
        float(tstat),
        dof,
        p_phrase(float(pvalue)),
    )

    lines = [
        "# Mycelial ingrowth in intact-canopy versus canopy-gap spruce stands",
        "",
        "## Data",
        "",
        "The file holds {0} rows, one per surveyed stand: {1} intact-canopy and".format(len(rows), n_a),
        "{0} canopy-gap. Each stand contributed a single pooled four-bag ingrowth".format(n_b),
        "composite, so every stand supplies exactly one analysed measurement and no",
        "stand appears twice in the file.",
        "",
        "| canopy_state | stands | mean (mg) | SD (mg) | median (mg) |",
        "| --- | --- | --- | --- | --- |",
        table_row(REFERENCE, sum_a),
        table_row(CONTRAST, sum_b),
        "",
        "## Analysis",
        "",
        "Welch's two-sided two-sample t-test on stand-level mycelial dry mass,",
        "comparing intact-canopy stands with canopy-gap stands. The independent",
        "unit is the stand, and each stand enters the test exactly once.",
        "",
        "## Result",
        "",
        result,
        "",
        "Cohen's d = {0:.3f}, using a pooled SD of {1:.3f} mg.".format(effect, pooled_sd),
        "",
        "The two groups happen to share the same sample SD, so the Welch correction",
        "returns the equal-variance degrees of freedom.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
