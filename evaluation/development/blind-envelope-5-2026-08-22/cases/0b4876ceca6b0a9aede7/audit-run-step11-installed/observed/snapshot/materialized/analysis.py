"""Grow-out feed comparison: fillet omega-3 (EPA+DHA) at harvest.

Reads harvest_fillet_omega3.csv, compares fillet omega-3 content between the
standard high-fishmeal feed and the reformulated algal-oil feed with an
independent two-sample t-test, and prints the results.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "harvest_fillet_omega3.csv")
OUTCOME = "omega3_mg_per_g"
ALPHA = 0.05


def main():
    df = pd.read_csv(DATA_FILE)

    standard = df.loc[df["feed"] == "standard", OUTCOME]
    algal = df.loc[df["feed"] == "algal_oil", OUTCOME]

    n_standard = len(standard)
    n_algal = len(algal)
    n_total = n_standard + n_algal

    mean_standard = standard.mean()
    mean_algal = algal.mean()
    sd_standard = standard.std(ddof=1)
    sd_algal = algal.std(ddof=1)
    se_standard = sd_standard / (n_standard ** 0.5)
    se_algal = sd_algal / (n_algal ** 0.5)
    difference = mean_algal - mean_standard

    # Independent two-sample t-test on the difference in means.
    # Every measured fish is entered as a separate observation.
    t_stat, p_value = stats.ttest_ind(algal, standard)
    df_resid = n_total - 2

    pooled_sd = (((n_algal - 1) * sd_algal ** 2 + (n_standard - 1) * sd_standard ** 2)
                 / df_resid) ** 0.5
    se_diff = pooled_sd * ((1.0 / n_algal + 1.0 / n_standard) ** 0.5)
    t_crit = stats.t.ppf(1 - ALPHA / 2, df_resid)
    ci_low = difference - t_crit * se_diff
    ci_high = difference + t_crit * se_diff
    cohens_d = difference / pooled_sd

    # Descriptive harvest weights, reported alongside the outcome.
    w_standard = df.loc[df["feed"] == "standard", "harvest_weight_kg"]
    w_algal = df.loc[df["feed"] == "algal_oil", "harvest_weight_kg"]

    print("Fillet omega-3 (EPA+DHA) at harvest: grow-out feed comparison")
    print("=" * 62)
    print(f"Data file            : {os.path.basename(DATA_FILE)}")
    print(f"Rows read            : {len(df)}")
    print(f"Cages represented    : {df['cage_id'].nunique()}")
    print(f"Measured fish in test: {n_total}")
    print()

    print("Group summaries (omega3_mg_per_g)")
    print("-" * 62)
    header = f"{'group':<12}{'n':>5}{'mean':>10}{'sd':>10}{'se':>9}{'min':>8}{'max':>8}"
    print(header)
    print(f"{'standard':<12}{n_standard:>5}{mean_standard:>10.3f}{sd_standard:>10.3f}"
          f"{se_standard:>9.3f}{standard.min():>8.2f}{standard.max():>8.2f}")
    print(f"{'algal_oil':<12}{n_algal:>5}{mean_algal:>10.3f}{sd_algal:>10.3f}"
          f"{se_algal:>9.3f}{algal.min():>8.2f}{algal.max():>8.2f}")
    print()

    print("Harvest weight (harvest_weight_kg)")
    print("-" * 62)
    print(f"{'standard':<12}{len(w_standard):>5}{w_standard.mean():>10.3f}"
          f"{w_standard.std(ddof=1):>10.3f}")
    print(f"{'algal_oil':<12}{len(w_algal):>5}{w_algal.mean():>10.3f}"
          f"{w_algal.std(ddof=1):>10.3f}")
    print()

    print("Independent two-sample t-test (algal_oil - standard)")
    print("-" * 62)
    print(f"Observations entered : {n_total} measured fish")
    print(f"Difference in means  : {difference:.3f} mg/g")
    print(f"95% CI of difference : [{ci_low:.3f}, {ci_high:.3f}] mg/g")
    print(f"Pooled SD            : {pooled_sd:.3f} mg/g")
    print(f"t statistic          : {t_stat:.3f}")
    print(f"Degrees of freedom   : {df_resid}")
    print(f"p-value              : {p_value:.6g}")
    print(f"Cohen's d            : {cohens_d:.3f}")
    print()

    verdict = "SIGNIFICANT" if p_value < ALPHA else "NOT SIGNIFICANT"
    print(f"Feed effect at alpha = {ALPHA}: {verdict}")


if __name__ == "__main__":
    main()
