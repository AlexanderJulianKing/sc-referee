"""Ocean acidification and juvenile Pacific oysters.

Oysters were reared for ten weeks at present-day pH (ambient) or at a lowered
pH matching an end-of-century projection, everything else matched, and measured
once at the end.

The panel of six outcomes is screened as a whole before any single outcome is
looked at. The screening statistic is the sum of the six squared standardised
mean differences (Cohen's d, pooled SD), and its null distribution is built by
reshuffling the treatment labels 2000 times. Only if the panel is extreme at
five percent do we go on to the per-outcome tests. If it is not, the script
stops and no per-outcome verdict is reported.
"""

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05
N_PERMUTATIONS = 2000
SEED = 20241014

OUTCOMES = [
    ("shell_length_mm", "shell length (mm)"),
    ("shell_thickness_um", "shell thickness (um)"),
    ("dry_tissue_mass_mg", "dry tissue mass (mg)"),
    ("calcification_rate_mg_d", "calcification (mg/day)"),
    ("respiration_umol_h", "respiration (umol/h)"),
    ("survival_days", "survival (days of 70)"),
]


def panel_statistic(values, is_low_ph):
    """Sum of squared standardised mean differences across the whole panel.

    `values` is oysters x outcomes; `is_low_ph` is a boolean mask over oysters.
    """
    low = values[is_low_ph]
    ambient = values[~is_low_ph]
    n_low = low.shape[0]
    n_ambient = ambient.shape[0]

    mean_difference = ambient.mean(axis=0) - low.mean(axis=0)
    pooled_variance = (
        (n_ambient - 1) * ambient.var(axis=0, ddof=1)
        + (n_low - 1) * low.var(axis=0, ddof=1)
    ) / (n_ambient + n_low - 2)
    standardised = mean_difference / np.sqrt(pooled_variance)
    return float(np.sum(standardised**2))


def main():
    oysters = pd.read_csv("data.csv")
    columns = [column for column, _ in OUTCOMES]
    values = oysters[columns].to_numpy(dtype=float)
    is_low_ph = (oysters["ph_treatment"] == "low_ph").to_numpy()

    print("Juvenile oysters, ten-week pH exposure")
    print(
        f"ambient: {(~is_low_ph).sum()} oysters   "
        f"low pH: {is_low_ph.sum()} oysters   panel of {len(OUTCOMES)} outcomes"
    )
    print()

    observed = panel_statistic(values, is_low_ph)

    rng = np.random.default_rng(SEED)
    null_statistics = np.empty(N_PERMUTATIONS)
    for i in range(N_PERMUTATIONS):
        shuffled = rng.permutation(is_low_ph)
        null_statistics[i] = panel_statistic(values, shuffled)

    # Permutation p-value, counting the observed arrangement itself.
    panel_p = (1 + np.sum(null_statistics >= observed)) / (1 + N_PERMUTATIONS)

    print("WHOLE-PANEL SCREEN (gate on the per-outcome tests)")
    print(f"panel statistic (sum of squared standardised differences): {observed:.3f}")
    print(f"permutations: {N_PERMUTATIONS}   panel p = {panel_p:.4g}")

    if panel_p >= ALPHA:
        print(
            f"panel p is not below {ALPHA}: the panel showed no overall effect of pH."
        )
        print("Per-outcome tests are not reported.")
        return

    print(f"panel p is below {ALPHA}: the gate is open, per-outcome tests follow.")
    print()

    print("PER-OUTCOME RESULTS (reported only because the panel test passed)")
    print(f"{'outcome':26s} {'ambient':>9s} {'low pH':>9s} {'p':>11s}  verdict")
    for column, label in OUTCOMES:
        ambient = oysters.loc[~is_low_ph, column]
        low = oysters.loc[is_low_ph, column]
        t_stat, p_value = stats.ttest_ind(ambient, low, equal_var=False)
        verdict = "significant" if p_value < ALPHA else "not significant"
        print(
            f"{label:26s} {ambient.mean():9.2f} {low.mean():9.2f} "
            f"{p_value:11.4g}  {verdict}"
        )


if __name__ == "__main__":
    main()
