"""Stomatal conductance of coffee shrubs under shade trees versus in full sun.

Reads the porometer table, compares the two canopy treatments with an
independent two-sample test of the difference in means, and prints the results.
Every measured leaf enters the comparison as a separate observation.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "coffee_stomatal_conductance.csv"
OUTCOME = "stomatal_conductance_mmol_m2_s"
GROUP = "canopy_treatment"


def main():
    df = pd.read_csv(DATA_FILE)

    shade = df.loc[df[GROUP] == "shade_trees", OUTCOME]
    full_sun = df.loc[df[GROUP] == "full_sun", OUTCOME]

    n_shade = len(shade)
    n_sun = len(full_sun)
    n_total = n_shade + n_sun

    mean_shade = shade.mean()
    mean_sun = full_sun.mean()
    sd_shade = shade.std(ddof=1)
    sd_sun = full_sun.std(ddof=1)
    se_shade = sd_shade / (n_shade ** 0.5)
    se_sun = sd_sun / (n_sun ** 0.5)

    diff = mean_shade - mean_sun

    # Independent two-sample t-test on the difference in means (Welch).
    t_stat, p_value = stats.ttest_ind(shade, full_sun, equal_var=False)

    # Welch confidence interval for the difference in means.
    se_diff = (se_shade ** 2 + se_sun ** 2) ** 0.5
    dof = (se_shade ** 2 + se_sun ** 2) ** 2 / (
        se_shade ** 4 / (n_shade - 1) + se_sun ** 4 / (n_sun - 1)
    )
    t_crit = stats.t.ppf(0.975, dof)
    ci_low = diff - t_crit * se_diff
    ci_high = diff + t_crit * se_diff

    print("Coffee stomatal conductance: shade trees vs full sun")
    print("=" * 56)
    print(f"Data file            : {DATA_FILE}")
    print(f"Leaves analysed (n)  : {n_total}")
    print()
    print("Group summaries (mmol H2O m-2 s-1)")
    print(f"  shade_trees : n = {n_shade:3d}   mean = {mean_shade:7.2f}   "
          f"SD = {sd_shade:6.2f}   SE = {se_shade:5.2f}   "
          f"range = {shade.min()} to {shade.max()}")
    print(f"  full_sun    : n = {n_sun:3d}   mean = {mean_sun:7.2f}   "
          f"SD = {sd_sun:6.2f}   SE = {se_sun:5.2f}   "
          f"range = {full_sun.min()} to {full_sun.max()}")
    print()
    print("Independent two-sample t-test (Welch), difference in means")
    print(f"  difference (shade - full sun) : {diff:.2f}")
    print(f"  95% CI for the difference     : {ci_low:.2f} to {ci_high:.2f}")
    print(f"  t                             : {t_stat:.4f}")
    print(f"  df                            : {dof:.2f}")
    print(f"  p-value                       : {p_value:.6g}")
    print()
    pct = 100.0 * diff / mean_sun
    print(f"Shaded shrubs exceed full-sun shrubs by {pct:.1f} percent.")
    if p_value < 0.05:
        print("Conclusion: shade raises stomatal conductance (p < 0.05).")
    else:
        print("Conclusion: no detected difference in stomatal conductance.")

    # Leaf temperature, recorded alongside each reading.
    print()
    print("Leaf temperature at measurement (deg C)")
    for level in ("shade_trees", "full_sun"):
        temps = df.loc[df[GROUP] == level, "leaf_temp_c"]
        print(f"  {level:12s}: mean = {temps.mean():5.2f}   "
              f"SD = {temps.std(ddof=1):4.2f}   "
              f"range = {temps.min():.1f} to {temps.max():.1f}")


if __name__ == "__main__":
    main()
