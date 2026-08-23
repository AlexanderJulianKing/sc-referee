"""Effect of maternal protein restriction on rat pup body mass at weaning (day 21).

The maternal diet was fed to the dam, so every pup in a litter shares one prenatal
exposure, one set of parents and one nursing environment. The litter, not the pup,
is therefore the independent experimental unit. This script reads the raw pup-level
records, collapses each litter to a single litter-average body mass, and compares
the 8 control litter averages against the 8 protein-restricted litter averages with
an independent two-sample Welch t-test (n = 16 litters).
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pup_masses.csv")

UNIT_COL = "litter_id"
GROUP_COL = "diet_group"
OUTCOME_COL = "body_mass_g"
CONTROL = "control"
RESTRICTED = "protein_restricted"


def main():
    # ---- 1. Raw pup-level data -------------------------------------------------
    pups = pd.read_csv(DATA_FILE)
    n_pup_records = len(pups)

    print("=" * 72)
    print("Maternal protein restriction and rat pup body mass at postnatal day 21")
    print("=" * 72)
    print()
    print("Data description (NOT the sample size of the comparison)")
    print("-" * 72)
    print(f"  Raw pup records read from pup_masses.csv : {n_pup_records}")
    print(f"  Distinct litters                          : {pups[UNIT_COL].nunique()}")
    print(f"  Pups weighed per litter                   : "
          f"{int(pups.groupby(UNIT_COL).size().unique()[0])}")
    print(f"  Female / male pups                        : "
          f"{int((pups['sex'] == 'F').sum())} / {int((pups['sex'] == 'M').sum())}")
    print()
    print("  The 128 pup rows are NOT 128 independent observations. Each litter")
    print("  occupies 8 rows, and those 8 rows share one dam, one diet exposure and")
    print("  one nursing environment. The pup count describes how many animals were")
    print("  weighed; it is not the n of the statistical comparison below.")
    print()

    # ---- 2. Reduce to one value per litter -------------------------------------
    # Each of the 16 litters contributes exactly one number: the mean day-21 body
    # mass of its 8 pups. All testing below is done on these 16 litter values.
    litters = (
        pups.groupby([UNIT_COL, GROUP_COL], as_index=False)[OUTCOME_COL]
        .mean()
        .rename(columns={OUTCOME_COL: "litter_mean_body_mass_g"})
        .sort_values(UNIT_COL)
        .reset_index(drop=True)
    )

    print("Aggregation to the experimental unit")
    print("-" * 72)
    print("  UNIT OF ANALYSIS = THE LITTER (the dam), not the individual pup.")
    print("  Each litter's 8 pup masses were averaged into one litter value before")
    print("  any group comparison was made.")
    print(f"  Litter values formed: {len(litters)}")
    print()
    print("  Litter averages (g):")
    for _, row in litters.iterrows():
        print(f"    {row[UNIT_COL]}  {row[GROUP_COL]:<19s} "
              f"{row['litter_mean_body_mass_g']:.2f}")
    print()

    ctrl = litters.loc[litters[GROUP_COL] == CONTROL, "litter_mean_body_mass_g"]
    restr = litters.loc[litters[GROUP_COL] == RESTRICTED, "litter_mean_body_mass_g"]

    # ---- 3. Independent two-sample comparison of the 16 litter values ----------
    n_ctrl, n_restr = len(ctrl), len(restr)
    mean_ctrl, mean_restr = ctrl.mean(), restr.mean()
    sd_ctrl, sd_restr = ctrl.std(ddof=1), restr.std(ddof=1)
    diff = mean_ctrl - mean_restr

    t_stat, p_value = stats.ttest_ind(ctrl, restr, equal_var=False)
    dof = ((sd_ctrl**2 / n_ctrl + sd_restr**2 / n_restr) ** 2) / (
        (sd_ctrl**2 / n_ctrl) ** 2 / (n_ctrl - 1)
        + (sd_restr**2 / n_restr) ** 2 / (n_restr - 1)
    )
    se_diff = (sd_ctrl**2 / n_ctrl + sd_restr**2 / n_restr) ** 0.5
    t_crit = stats.t.ppf(0.975, dof)
    ci_low, ci_high = diff - t_crit * se_diff, diff + t_crit * se_diff

    print("Group comparison: independent two-sample Welch t-test on litter averages")
    print("-" * 72)
    print(f"  Sample size, control            : {n_ctrl} litters")
    print(f"  Sample size, protein-restricted : {n_restr} litters")
    print(f"  Sample size, total              : {n_ctrl + n_restr} litters")
    print("  (Sample size counts LITTERS. The 128 pups are not the sample size.)")
    print()
    print(f"  Mean of control litter averages            : {mean_ctrl:.2f} g")
    print(f"  Mean of protein-restricted litter averages : {mean_restr:.2f} g")
    print(f"  SD of control litter averages              : {sd_ctrl:.2f} g")
    print(f"  SD of protein-restricted litter averages   : {sd_restr:.2f} g")
    print()
    print(f"  Difference in means (control - restricted) : {diff:.2f} g")
    print(f"  95% CI for the difference                  : "
          f"[{ci_low:.2f}, {ci_high:.2f}] g")
    print(f"  Welch t statistic                          : {t_stat:.3f}")
    print(f"  Welch degrees of freedom                   : {dof:.2f}")
    print(f"  p-value (two-sided)                        : {p_value:.6f}")
    print()
    print(f"  Relative reduction at weaning              : "
          f"{100 * diff / mean_ctrl:.1f}% of the control mean")
    print("=" * 72)


if __name__ == "__main__":
    main()
