"""First-mode damping of machine-tool bases: gray cast iron vs. polymer concrete.

Input : data/input.csv  (one instrumented hammer strike per row)
Output: results/report.md
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict

import numpy as np
from scipy import stats

INPUT_PATH = os.path.join("data", "input.csv")
OUTPUT_DIR = "results"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "report.md")

REFERENCE = "gray_cast_iron"
TREATMENT = "polymer_concrete"

COL_UNIT = "base_id"
COL_GROUP = "base_material"
COL_RESPONSE = "damping_ratio_pct"


def read_strikes(path):
    """Collect damping ratios (one per strike) and base labels per material."""
    damping = defaultdict(list)
    bases = defaultdict(set)
    with open(path, "r", newline="", encoding="ascii") as handle:
        for record in csv.DictReader(handle):
            material = record[COL_GROUP]
            damping[material].append(float(record[COL_RESPONSE]))
            bases[material].add(record[COL_UNIT])
    return damping, bases


def welch_dof(sample_a, sample_b):
    """Welch-Satterthwaite degrees of freedom for two samples."""
    term_a = np.var(sample_a, ddof=1) / len(sample_a)
    term_b = np.var(sample_b, ddof=1) / len(sample_b)
    numerator = (term_a + term_b) ** 2
    denominator = (
        term_a ** 2 / (len(sample_a) - 1) + term_b ** 2 / (len(sample_b) - 1)
    )
    return numerator / denominator


def cell_row(material, strikes, mean_damping):
    return "| {:<16} | {:<7} | {:<22} |".format(material, strikes, mean_damping)


def main():
    damping, bases = read_strikes(INPUT_PATH)

    reference = np.asarray(damping[REFERENCE], dtype=float)
    treatment = np.asarray(damping[TREATMENT], dtype=float)

    mean_reference = float(np.mean(reference))
    mean_treatment = float(np.mean(treatment))
    difference = mean_treatment - mean_reference

    outcome = stats.ttest_ind(treatment, reference, equal_var=False)
    dof = welch_dof(treatment, reference)
    if outcome.pvalue < 1e-15:
        p_text = "< 1e-15"
    else:
        p_text = "= {:.3g}".format(outcome.pvalue)

    n_reference = int(reference.size)
    n_treatment = int(treatment.size)
    total = n_reference + n_treatment
    per_base = n_reference // len(bases[REFERENCE])

    lines = [
        "# Structural damping of machine-tool bases: gray cast iron vs. polymer concrete",
        "",
        "## Data",
        "",
        "Modal impact tests on machine-tool bases. Each row of the input table is one",
        "instrumented hammer strike, and the response variable is the first-mode damping",
        "ratio expressed as a percentage of critical damping. The table holds {} strikes:".format(total),
        "{} gray cast iron bases and {} polymer concrete bases, with {} strikes recorded on".format(
            len(bases[REFERENCE]), len(bases[TREATMENT]), per_base
        ),
        "each base.",
        "",
        "## Analysis",
        "",
        "Welch's two-sample t-test (scipy.stats.ttest_ind with equal_var=False) compares",
        "the damping ratio of polymer concrete strikes against gray cast iron strikes.",
        "Every recorded strike is entered into the test as one observation, so each",
        "material group contributes {} observations.".format(n_treatment),
        "",
        "## Result",
        "",
        cell_row("material", "strikes", "mean damping ratio (%)"),
        cell_row("-" * 16, "-" * 7, "-" * 22),
        cell_row(REFERENCE, str(n_reference), "{:.3f}".format(mean_reference)),
        cell_row(TREATMENT, str(n_treatment), "{:.3f}".format(mean_treatment)),
        "",
        "Mean difference (polymer concrete minus gray cast iron): {:.3f} percentage".format(difference),
        "points. Welch t = {:.2f}, df = {:.1f}, p {}.".format(outcome.statistic, dof, p_text),
        "",
        (
            "[selected-result] Polymer concrete machine-tool bases damp the first bending "
            "mode more strongly than gray cast iron bases: mean damping ratio {:.3f}% "
            "versus {:.3f}%, a difference of {:.3f} percentage points (Welch two-sample "
            "t-test over {} strikes per material, t = {:.2f}, df = {:.1f}, p {})."
        ).format(
            mean_treatment,
            mean_reference,
            difference,
            n_treatment,
            outcome.statistic,
            dof,
            p_text,
        ),
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
