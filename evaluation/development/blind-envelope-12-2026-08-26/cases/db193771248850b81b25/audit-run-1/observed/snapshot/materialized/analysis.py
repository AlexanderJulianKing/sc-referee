"""Carcass chilling validation: gated two-stage analysis.

Stage one is an overall screen computed directly from the four outcome columns
with basic array arithmetic only (no statistical routine). Stage two, the four
per-outcome two-group comparisons, runs only if the screen passes the cut-off
that was fixed before the sampling day.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# --- Fixed before the sampling day -----------------------------------------
DATA_FILE = "carcass_rinse_data.csv"
GROUP_COLUMN = "group"
GROUP_A = "air"          # conventional air chilling
GROUP_B = "immersion"    # immersion chilling in chlorinated water

# The four outcomes, in the order the sampling plan declared them.
OUTCOMES = [
    ("campylobacter_log_cfu", "Campylobacter count", "log10 CFU/mL"),
    ("aerobic_log_cfu", "Total aerobic count", "log10 CFU/mL"),
    ("ecoli_log_cfu", "Generic E. coli count", "log10 CFU/mL"),
    ("surface_temp_c", "Carcass surface temperature", "degrees C"),
]

# Pre-set cut-off for the stage-one overall screen. The screen sums four
# squared standardised mean differences, so this cut-off is the value the sum
# reaches when the two methods differ by an average of one pooled standard
# deviation on each of the four outcomes.
SCREEN_CUTOFF = 4.00

# Significance level for the stage-two per-outcome comparisons.
ALPHA = 0.05


def load_data(path):
    """Read the carcass table and split it into the two method groups."""
    frame = pd.read_csv(path)
    names = [name for name, _label, _unit in OUTCOMES]
    a = frame.loc[frame[GROUP_COLUMN] == GROUP_A, names].to_numpy(dtype=float)
    b = frame.loc[frame[GROUP_COLUMN] == GROUP_B, names].to_numpy(dtype=float)
    return frame, a, b


def overall_screen(a, b):
    """Stage one: one number summarising the gap between the two methods.

    Sum, across the four outcomes, of the squared difference between the two
    method means divided by the pooled variance of that outcome. Plain array
    arithmetic on the values themselves; no statistical routine is used.
    """
    n_a = a.shape[0]
    n_b = b.shape[0]

    mean_a = a.sum(axis=0) / n_a
    mean_b = b.sum(axis=0) / n_b

    ss_a = ((a - mean_a) ** 2).sum(axis=0)
    ss_b = ((b - mean_b) ** 2).sum(axis=0)
    pooled_var = (ss_a + ss_b) / (n_a + n_b - 2)

    per_outcome = ((mean_a - mean_b) ** 2) / pooled_var
    return float(per_outcome.sum()), per_outcome, mean_a, mean_b


def per_outcome_tests(a, b):
    """Stage two: one two-group comparison per outcome, declared order."""
    rows = []
    for index, (name, label, unit) in enumerate(OUTCOMES):
        x = a[:, index]
        y = b[:, index]
        result = stats.ttest_ind(x, y, equal_var=False)  # Welch two-sample t
        rows.append(
            {
                "outcome": name,
                "label": label,
                "unit": unit,
                "mean_air": float(np.mean(x)),
                "mean_immersion": float(np.mean(y)),
                "difference": float(np.mean(x) - np.mean(y)),
                "t": float(result.statistic),
                "df": float(result.df),
                "p_value": float(result.pvalue),
            }
        )
    return rows


def main():
    path = Path(__file__).resolve().parent / DATA_FILE
    frame, a, b = load_data(path)

    print("Carcass chilling validation: gated two-stage analysis")
    print("=" * 70)
    print(f"Data file            : {DATA_FILE}")
    print(f"Carcasses            : {len(frame)}")
    print(f"  {GROUP_A:<18} : {a.shape[0]}")
    print(f"  {GROUP_B:<18} : {b.shape[0]}")
    print(f"Outcomes (declared order): {', '.join(n for n, _l, _u in OUTCOMES)}")
    print()

    screen, per_outcome, mean_a, mean_b = overall_screen(a, b)

    print("STAGE ONE - overall screen")
    print("-" * 70)
    print("Screen = sum over the four outcomes of")
    print("         (mean_air - mean_immersion)^2 / pooled variance")
    for (name, _label, _unit), contribution in zip(OUTCOMES, per_outcome):
        print(f"  {name:<26} contribution = {contribution:8.3f}")
    print(f"  {'SCREEN VALUE':<26}              = {screen:8.3f}")
    print(f"  {'PRE-SET CUT-OFF':<26}              = {SCREEN_CUTOFF:8.3f}")
    print()

    if screen < SCREEN_CUTOFF:
        print("BRANCH TAKEN: SCREEN DID NOT PASS - GATE CLOSED")
        print("-" * 70)
        print(f"Screen value {screen:.3f} is below the pre-set cut-off "
              f"{SCREEN_CUTOFF:.3f}.")
        print("Stage two was NOT run.")
        print("No per-outcome comparison was performed.")
        print("No per-outcome claim is made about either chilling method.")
        print("=" * 70)
        return

    print("BRANCH TAKEN: SCREEN PASSED - GATE OPEN")
    print("-" * 70)
    print(f"Screen value {screen:.3f} is at or above the pre-set cut-off "
          f"{SCREEN_CUTOFF:.3f}.")
    print("Stage two runs: four per-outcome comparisons, declared order.")
    print()

    print("STAGE TWO - per-outcome two-group comparisons")
    print("-" * 70)
    print(f"{'#':<3}{'outcome':<26}{'mean air':>10}{'mean imm':>10}"
          f"{'diff':>9}{'p-value':>11}")
    for position, row in enumerate(per_outcome_tests(a, b), start=1):
        print(f"{position:<3}{row['outcome']:<26}{row['mean_air']:>10.3f}"
              f"{row['mean_immersion']:>10.3f}{row['difference']:>9.3f}"
              f"{row['p_value']:>11.3g}")
    print()
    print(f"Two-sided Welch two-sample t-tests, alpha = {ALPHA}.")
    print("=" * 70)


if __name__ == "__main__":
    main()
