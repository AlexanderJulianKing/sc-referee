"""Ferret housing-enrichment welfare study: analysis of the four declared outcomes.

Reads ferret_welfare.csv (one row per ferret) and analyses the four welfare
outcomes declared in the welfare assessment plan, in their declared order.

Order of operations, fixed before the data were seen:

  1. Describe the colony: number of ferrets per housing condition, and the mean
     and standard deviation of each outcome within each condition.
  2. Compute ONE overall screening quantity that summarises how far apart the
     two housing conditions are across all four outcomes taken together. It is
     computed from the outcome columns with plain array arithmetic only: each
     outcome's group difference is divided by that outcome's own pooled
     standard deviation, and the four resulting standardised separations are
     combined into a single root-mean-square value. No statistical test, no
     p-value and no significance machinery is used at this step.
  3. Compare the screening quantity with a cutoff that was fixed in advance.
       - Below the cutoff: the study stops at the overall screen. No
         per-outcome comparison is run and no per-outcome verdict is stated.
       - At or above the cutoff: the standard two-group significance test
         (Welch's two-sample t-test) is run for each declared outcome and each
         p-value is judged at the conventional 0.05 threshold.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# --- Configuration fixed in advance ----------------------------------------

DATA_FILE = Path(__file__).resolve().parent / "ferret_welfare.csv"

GROUP_COLUMN = "housing_condition"
ENRICHED = "enriched"
STANDARD = "standard"

# The four outcomes, in the order the welfare assessment plan declared them.
OUTCOMES = [
    ("daily_active_time_min", "Daily active time (min/day)"),
    ("faecal_corticosterone_ng_per_g", "Faecal corticosterone (ng/g)"),
    ("body_mass_change_g", "Body mass change (g)"),
    ("stereotypic_bouts_per_hour", "Stereotypic bouts (per hour)"),
]

# Cutoff for the overall screening quantity, fixed before any per-outcome
# comparison is run. The screening quantity is the root-mean-square of the four
# outcomes' standardised group separations, so it is on the familiar effect-size
# scale where 0.2 is small, 0.5 is medium and 0.8 is large. The screen is meant
# to ask whether the housing conditions differ at all as a family, so the cutoff
# is set at a modest, clearly-not-nothing level.
SCREEN_CUTOFF = 0.40

ALPHA = 0.05


# --- Helpers ---------------------------------------------------------------


def pooled_sd(values_a: np.ndarray, values_b: np.ndarray) -> float:
    """Pooled standard deviation of two samples, by ordinary array arithmetic."""
    n_a = values_a.size
    n_b = values_b.size
    var_a = values_a.var(ddof=1)
    var_b = values_b.var(ddof=1)
    return float(np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)))


def standardised_separation(values_a: np.ndarray, values_b: np.ndarray) -> float:
    """Group mean difference expressed in pooled standard deviations."""
    return float((values_a.mean() - values_b.mean()) / pooled_sd(values_a, values_b))


def main() -> None:
    data = pd.read_csv(DATA_FILE)

    enriched = data[data[GROUP_COLUMN] == ENRICHED]
    standard = data[data[GROUP_COLUMN] == STANDARD]

    # --- 1. Colony description --------------------------------------------
    print("=" * 72)
    print("FERRET HOUSING-ENRICHMENT WELFARE STUDY")
    print("=" * 72)
    print()
    print(f"Data file: {DATA_FILE.name}")
    print(f"Ferrets in file: {len(data)}")
    print()
    print("Group sizes")
    print("-" * 72)
    for label, frame in ((ENRICHED, enriched), (STANDARD, standard)):
        print(f"  {label:<10s} n = {len(frame)}")
    print()

    print("Per-group summary of each declared outcome (mean, SD)")
    print("-" * 72)
    header = f"  {'outcome':<32s} {'group':<10s} {'n':>3s} {'mean':>9s} {'SD':>8s}"
    print(header)
    for column, label in OUTCOMES:
        for group_label, frame in ((ENRICHED, enriched), (STANDARD, standard)):
            values = frame[column].to_numpy(dtype=float)
            print(
                f"  {label:<32s} {group_label:<10s} {values.size:>3d} "
                f"{values.mean():>9.2f} {values.std(ddof=1):>8.2f}"
            )
    print()

    # --- 2. Overall screen, computed before any per-outcome comparison ----
    # Plain array arithmetic only: no test, no p-value, no significance
    # machinery is involved in producing this number.
    separations = []
    for column, _label in OUTCOMES:
        separations.append(
            standardised_separation(
                enriched[column].to_numpy(dtype=float),
                standard[column].to_numpy(dtype=float),
            )
        )
    separations = np.asarray(separations, dtype=float)
    overall_screen = float(np.sqrt(np.mean(separations**2)))

    print("OVERALL SCREEN (computed first, before any per-outcome comparison)")
    print("-" * 72)
    print("  Standardised separation of the two housing conditions, per outcome:")
    for (column, label), separation in zip(OUTCOMES, separations):
        print(f"    {label:<32s} {separation:+.3f}")
    print()
    print("  Overall screening quantity (root-mean-square of the four above)")
    print(f"    value  = {overall_screen:.3f}")
    print(f"    cutoff = {SCREEN_CUTOFF:.3f}   (fixed in advance)")
    print()

    # --- 3. The two branches ----------------------------------------------
    if overall_screen < SCREEN_CUTOFF:
        print("*" * 72)
        print("BRANCH TAKEN: SCREEN NOT CLEARED - STUDY STOPS HERE")
        print("*" * 72)
        print(
            f"  The overall screening quantity ({overall_screen:.3f}) is below the\n"
            f"  cutoff fixed in advance ({SCREEN_CUTOFF:.3f}). The two housing\n"
            "  conditions are not far enough apart across the four declared\n"
            "  outcomes taken together to go further."
        )
        print()
        print("  No per-outcome comparison is run.")
        print("  No per-outcome p-value is computed.")
        print("  No per-outcome verdict is stated.")
        print()
        return

    print("*" * 72)
    print("BRANCH TAKEN: SCREEN CLEARED - PER-OUTCOME COMPARISONS PROCEED")
    print("*" * 72)
    print(
        f"  The overall screening quantity ({overall_screen:.3f}) is at or above the\n"
        f"  cutoff fixed in advance ({SCREEN_CUTOFF:.3f}), so each declared outcome\n"
        "  is now compared between the two housing conditions with the standard\n"
        "  two-group significance test (Welch's two-sample t-test)."
    )
    print()
    print(f"Per-outcome comparisons, judged at alpha = {ALPHA}")
    print("-" * 72)
    print(
        f"  {'outcome':<32s} {'enriched':>9s} {'standard':>9s} "
        f"{'t':>7s} {'p':>9s}  verdict"
    )
    for column, label in OUTCOMES:
        enriched_values = enriched[column].to_numpy(dtype=float)
        standard_values = standard[column].to_numpy(dtype=float)
        t_stat, p_value = stats.ttest_ind(
            enriched_values, standard_values, equal_var=False
        )
        verdict = "significant" if p_value < ALPHA else "not significant"
        print(
            f"  {label:<32s} {enriched_values.mean():>9.2f} "
            f"{standard_values.mean():>9.2f} {t_stat:>7.2f} {p_value:>9.4f}  {verdict}"
        )
    print()


if __name__ == "__main__":
    main()
