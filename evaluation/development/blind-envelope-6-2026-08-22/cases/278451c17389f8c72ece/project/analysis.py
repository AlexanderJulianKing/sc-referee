"""Butterhead lettuce nutrient formulation trial: harvest analysis.

Reads the harvest record, summarises head fresh mass under each nutrient
formulation, and compares the two formulations with an independent
two-sample t-test.
"""

import os

import pandas as pd
from scipy import stats

CSV_NAME = "lettuce_harvest.csv"

STANDARD = "standard"
RAISED_K = "raised_potassium"

MASS = "head_fresh_mass_g"


def load_harvest():
    """Read the harvest record that sits beside this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    frame = pd.read_csv(os.path.join(here, CSV_NAME))
    frame["harvest_date"] = pd.to_datetime(frame["harvest_date"]).dt.date
    return frame


def summarise(masses):
    """Descriptive statistics for one formulation's harvested heads."""
    n = int(masses.size)
    sd = float(masses.std(ddof=1))
    return {
        "n_heads": n,
        "mean_g": float(masses.mean()),
        "sd_g": sd,
        "se_g": sd / (n ** 0.5),
        "min_g": float(masses.min()),
        "median_g": float(masses.median()),
        "max_g": float(masses.max()),
    }


def describe_trial(frame):
    """Report the scale of the harvest that was cut and weighed."""
    print("=" * 68)
    print("BUTTERHEAD LETTUCE NUTRIENT FORMULATION TRIAL")
    print("=" * 68)
    print()
    print("Harvested heads weighed : {}".format(len(frame)))
    print("Growing gutters cut     : {}".format(frame["gutter_code"].nunique()))
    print("Plant positions per gutter: {}".format(
        frame["position_along_gutter"].nunique()))
    print("Harvest mornings        : {}".format(
        ", ".join(str(d) for d in sorted(frame["harvest_date"].unique()))))
    print()


def report_summary(label, stats_dict):
    print("  {:<18} n = {:>3} heads".format(label, stats_dict["n_heads"]))
    print("    mean head fresh mass : {:8.2f} g".format(stats_dict["mean_g"]))
    print("    standard deviation   : {:8.2f} g".format(stats_dict["sd_g"]))
    print("    standard error       : {:8.2f} g".format(stats_dict["se_g"]))
    print("    minimum / median / maximum : {:.1f} / {:.1f} / {:.1f} g".format(
        stats_dict["min_g"], stats_dict["median_g"], stats_dict["max_g"]))
    print()


def main():
    frame = load_harvest()
    describe_trial(frame)

    standard_masses = frame.loc[frame["formulation"] == STANDARD, MASS]
    raised_masses = frame.loc[frame["formulation"] == RAISED_K, MASS]

    standard_stats = summarise(standard_masses)
    raised_stats = summarise(raised_masses)

    print("HEAD FRESH MASS BY FORMULATION")
    print("-" * 68)
    report_summary("standard", standard_stats)
    report_summary("raised potassium", raised_stats)

    difference = raised_stats["mean_g"] - standard_stats["mean_g"]
    percent_gain = 100.0 * difference / standard_stats["mean_g"]

    # Independent two-sample t-test comparing the harvested heads grown under
    # the two formulations. Every head that was cut and weighed is entered as
    # its own observation, so the sample size for each formulation is the
    # total number of harvested heads carrying that formulation.
    t_stat, p_value = stats.ttest_ind(
        raised_masses, standard_masses, equal_var=True)

    n_raised = raised_stats["n_heads"]
    n_standard = standard_stats["n_heads"]
    df = n_raised + n_standard - 2

    pooled_var = (
        (n_raised - 1) * raised_stats["sd_g"] ** 2
        + (n_standard - 1) * standard_stats["sd_g"] ** 2
    ) / df
    pooled_sd = pooled_var ** 0.5
    se_difference = pooled_sd * ((1.0 / n_raised + 1.0 / n_standard) ** 0.5)

    t_critical = stats.t.ppf(0.975, df)
    ci_low = difference - t_critical * se_difference
    ci_high = difference + t_critical * se_difference

    cohens_d = difference / pooled_sd

    print("INDEPENDENT TWO-SAMPLE t-TEST (raised potassium vs standard)")
    print("-" * 68)
    print("  Observations entered   : every harvested head")
    print("  Sample sizes           : n = {} heads (raised potassium),"
          " n = {} heads (standard)".format(n_raised, n_standard))
    print("  Mean difference        : {:+.2f} g".format(difference))
    print("  Relative change        : {:+.2f} %".format(percent_gain))
    print("  Pooled SD              : {:.2f} g".format(pooled_sd))
    print("  SE of difference       : {:.2f} g".format(se_difference))
    print("  95% CI for difference  : [{:+.2f}, {:+.2f}] g".format(
        ci_low, ci_high))
    print("  t({})                  = {:.3f}".format(df, t_stat))
    print("  p-value                = {:.3e}".format(p_value))
    print("  Cohen's d              = {:.3f}".format(cohens_d))
    print()

    verdict = "significant" if p_value < 0.05 else "not significant"
    print("  At the 5% level the difference in head fresh mass is {}.".format(
        verdict))
    print()


if __name__ == "__main__":
    main()
