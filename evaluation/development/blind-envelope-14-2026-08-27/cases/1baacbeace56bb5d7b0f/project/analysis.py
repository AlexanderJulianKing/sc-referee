"""Gated two-stage analysis of the mango edible-coating shelf-life trial.

Stage 1 is an overall screen computed with elementary array arithmetic only:
the largest absolute standardised difference between the coated and uncoated
group means across the five pre-declared outcome columns. No statistical test,
p-value, model, or statistics-library routine is used in Stage 1.

Stage 2 runs only if the Stage 1 screen passes. It compares the two coating
groups on each of the five pre-declared outcomes with a two-sample Welch t-test
and controls the family-wise error rate over the complete outcome family with
the Holm step-down procedure, as required by PROTOCOL.md.
"""

import sys

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = "mango_coating_shelf_life.csv"
GROUP_COLUMN = "coating"
GROUP_A = "coated"
GROUP_B = "uncoated"

# The five pack-level outcomes, in the order the laboratory declared them.
OUTCOMES = [
    ("firmness_n", "Slice firmness (N)"),
    ("browning_index", "Surface browning index (0-100)"),
    ("tss_brix", "Total soluble solids (degrees Brix)"),
    ("weight_loss_pct", "Pack weight loss (%)"),
    ("aerobic_count_log10_cfu_per_g", "Aerobic plate count (log10 CFU/g)"),
]

SCREEN_THRESHOLD = 0.5
FAMILY_ALPHA = 0.05


def rule(char="="):
    print(char * 78)


def load_data():
    frame = pd.read_csv(DATA_FILE)
    coated = frame[frame[GROUP_COLUMN] == GROUP_A]
    uncoated = frame[frame[GROUP_COLUMN] == GROUP_B]
    return frame, coated, uncoated


def standardised_difference(values_a, values_b):
    """Absolute standardised mean difference from elementary array arithmetic.

    Group means, group spreads, a difference, a ratio, and an absolute value.
    No statistical test, no p-value, no model, no statistics-library routine.
    """
    mean_a = values_a.mean()
    mean_b = values_b.mean()
    n_a = values_a.size
    n_b = values_b.size
    var_a = ((values_a - mean_a) ** 2).sum() / (n_a - 1)
    var_b = ((values_b - mean_b) ** 2).sum() / (n_b - 1)
    pooled_sd = (((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)) ** 0.5
    return abs(mean_a - mean_b) / pooled_sd


def stage_one_screen(coated, uncoated):
    """Return (screening number, passed flag, per-outcome screen values)."""
    rule()
    print("STAGE 1: OVERALL SCREEN (no per-outcome comparison performed yet)")
    rule()
    print(
        "Screen statistic: largest absolute standardised difference between the\n"
        "coated and uncoated group means across all five declared outcomes.\n"
        f"Screen passes when that number is at least {SCREEN_THRESHOLD:.2f}.\n"
    )

    per_outcome = []
    print(f"{'Outcome':<34}{'mean coated':>13}{'mean uncoated':>15}{'|std diff|':>13}")
    print("-" * 78)
    for column, label in OUTCOMES:
        values_a = coated[column].to_numpy(dtype=float)
        values_b = uncoated[column].to_numpy(dtype=float)
        value = standardised_difference(values_a, values_b)
        per_outcome.append((column, label, value))
        print(
            f"{label:<34}{values_a.mean():>13.3f}{values_b.mean():>15.3f}{value:>13.3f}"
        )
    print("-" * 78)

    screening_number = max(value for _, _, value in per_outcome)
    driver = max(per_outcome, key=lambda row: row[2])[1]
    passed = screening_number >= SCREEN_THRESHOLD

    print(f"\nSCREENING NUMBER = {screening_number:.3f}  (largest of the five above)")
    print(f"Driven by: {driver}")
    print(f"Threshold  = {SCREEN_THRESHOLD:.2f}")
    print(f"SCREEN RESULT: {'PASSED' if passed else 'DID NOT PASS'}")
    return screening_number, passed, per_outcome


def welch_test(values_a, values_b):
    mean_a = values_a.mean()
    mean_b = values_b.mean()
    n_a = values_a.size
    n_b = values_b.size
    var_a = values_a.var(ddof=1)
    var_b = values_b.var(ddof=1)
    t_stat, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)
    # Welch-Satterthwaite degrees of freedom, reported for transparency.
    df = (var_a / n_a + var_b / n_b) ** 2 / (
        (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    )
    return mean_a - mean_b, float(t_stat), float(df), float(p_value)


def holm_adjust(p_values):
    """Holm step-down adjusted p-values over the complete outcome family."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, index in enumerate(order):
        candidate = (m - rank) * p_values[index]
        running = max(running, candidate)
        adjusted[index] = min(1.0, running)
    return adjusted


def stage_two_comparisons(coated, uncoated):
    rule()
    print("STAGE 2: PER-OUTCOME COMPARISONS (this branch ran: SCREEN PASSED)")
    rule()
    print(
        "Two-sample Welch t-test on each of the five pre-declared outcomes.\n"
        "The five outcomes form one family, so the family-wise error rate is\n"
        f"controlled across all five by the Holm procedure at alpha = {FAMILY_ALPHA:.2f}.\n"
        "Difference is reported as coated minus uncoated.\n"
    )

    rows = []
    for column, label in OUTCOMES:
        values_a = coated[column].to_numpy(dtype=float)
        values_b = uncoated[column].to_numpy(dtype=float)
        diff, t_stat, df, p_value = welch_test(values_a, values_b)
        rows.append([column, label, values_a.mean(), values_b.mean(), diff, t_stat, df, p_value])

    adjusted = holm_adjust([row[7] for row in rows])
    for row, p_adj in zip(rows, adjusted):
        row.append(p_adj)
        row.append("significant" if p_adj < FAMILY_ALPHA else "not significant")

    header = (
        f"{'Outcome':<34}{'coated':>9}{'uncoated':>10}{'diff':>9}"
        f"{'t':>8}{'df':>7}{'p raw':>10}{'p Holm':>10}  verdict"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        _, label, mean_a, mean_b, diff, t_stat, df, p_raw, p_adj, verdict = row
        print(
            f"{label:<34}{mean_a:>9.2f}{mean_b:>10.2f}{diff:>9.2f}"
            f"{t_stat:>8.2f}{df:>7.1f}{p_raw:>10.4g}{p_adj:>10.4g}  {verdict}"
        )
    print("-" * len(header))
    return rows


def main():
    frame, coated, uncoated = load_data()

    rule()
    print("MANGO EDIBLE COATING SHELF-LIFE TRIAL: GATED TWO-STAGE ANALYSIS")
    rule()
    print(f"Data file: {DATA_FILE}")
    print(f"Packs: {len(frame)} total, {len(coated)} coated, {len(uncoated)} uncoated")
    print(f"Missing values in the five outcome columns: "
          f"{int(frame[[c for c, _ in OUTCOMES]].isna().sum().sum())}")
    print(
        "\nGate: the per-outcome comparisons in Stage 2 are performed only if the\n"
        "Stage 1 overall screen passes. If the screen does not pass, the analysis\n"
        "stops and no per-outcome result is produced.\n"
    )

    screening_number, passed, _ = stage_one_screen(coated, uncoated)
    print()

    if not passed:
        rule()
        print("BRANCH TAKEN: SCREEN DID NOT PASS")
        rule()
        print(
            f"The overall screen did not pass: the screening number "
            f"{screening_number:.3f} is below the threshold {SCREEN_THRESHOLD:.2f}.\n"
            "No per-outcome comparisons were performed and no per-outcome results\n"
            "exist for this run."
        )
        rule()
        return 0

    stage_two_comparisons(coated, uncoated)
    print()
    rule()
    print("END OF ANALYSIS")
    rule()
    return 0


if __name__ == "__main__":
    sys.exit(main())
