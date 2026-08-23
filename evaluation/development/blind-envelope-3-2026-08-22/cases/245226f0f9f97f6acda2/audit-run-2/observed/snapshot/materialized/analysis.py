"""Analysis of the preclinical tumour-growth experiment.

Reads tumour_volumes.csv (24 rats, 5 weekly calliper measurements each, 120 rows)
and produces two clearly separated outputs.

PRIMARY (inferential) analysis
    A linear mixed-effects model of tumour volume on treatment group and week
    with a per-animal random intercept:

        tumour_volume_mm3 ~ treatment_group + week,  random intercept by animal_id

    The five measurements from one animal are not independent of one another,
    so the random intercept is what keeps the treatment standard error honest.
    The study's result is the treatment coefficient and its p-value from this
    model. Sample size is 24 animals contributing 120 measurements.

SECONDARY (sensitivity) check, NOT the inferential result
    A plain two-sample Welch t-test on the week-5 volumes only, treating the
    24 final-week rows as independent. This is reported for support and
    comparison; it is not the study's conclusion.

Run with:  /usr/local/bin/python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.formula.api as smf

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tumour_volumes.csv")

REFERENCE_GROUP = "vehicle"
COMPARISON_GROUP = "treated"


def load_data(path):
    """Read the CSV and check the structure the analysis assumes."""
    df = pd.read_csv(path)

    expected_columns = [
        "animal_id",
        "treatment_group",
        "week",
        "tumour_volume_mm3",
        "body_weight_g",
        "cage",
    ]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError("missing expected column(s): %s" % ", ".join(missing))

    if df[expected_columns].isna().any().any():
        raise ValueError("data contain missing cells; the analysis assumes none")

    # treatment_group is a two-level factor with vehicle as the reference level,
    # so the treatment coefficient reads as treated minus vehicle.
    levels = sorted(df["treatment_group"].unique())
    if levels != sorted([REFERENCE_GROUP, COMPARISON_GROUP]):
        raise ValueError("treatment_group levels are %s, expected %s and %s"
                         % (levels, REFERENCE_GROUP, COMPARISON_GROUP))
    df["treatment_group"] = pd.Categorical(
        df["treatment_group"], categories=[REFERENCE_GROUP, COMPARISON_GROUP], ordered=False
    )

    return df


def describe_design(df):
    """Print the design facts the inference depends on."""
    n_animals = df["animal_id"].nunique()
    n_rows = len(df)
    rows_per_animal = df.groupby("animal_id", observed=True).size()
    weeks = sorted(df["week"].unique())

    print("=" * 72)
    print("DESIGN AND DATA")
    print("=" * 72)
    print("Data file                     : %s" % os.path.basename(DATA_FILE))
    print("Animals (experimental units)  : %d" % n_animals)
    print("Measurements (rows)           : %d" % n_rows)
    print("Measurements per animal       : min %d, max %d"
          % (rows_per_animal.min(), rows_per_animal.max()))
    print("Weeks observed                : %s" % ", ".join(str(w) for w in weeks))
    print("Cages                         : %d" % df["cage"].nunique())
    print()

    animals_per_group = df.groupby("treatment_group", observed=True)["animal_id"].nunique()
    rows_per_group = df.groupby("treatment_group", observed=True).size()
    print("Animals per group:")
    for group in [REFERENCE_GROUP, COMPARISON_GROUP]:
        print("  %-8s : %2d animals, %3d measurements"
              % (group, animals_per_group[group], rows_per_group[group]))
    print()

    print("Mean tumour volume (mm3) by group and week:")
    cell_means = df.pivot_table(
        index="week", columns="treatment_group", values="tumour_volume_mm3",
        aggfunc="mean", observed=True,
    )
    print("  week   %-10s %-10s   difference" % (REFERENCE_GROUP, COMPARISON_GROUP))
    for week in weeks:
        veh = cell_means.loc[week, REFERENCE_GROUP]
        trt = cell_means.loc[week, COMPARISON_GROUP]
        print("  %4d   %10.1f %10.1f   %10.1f" % (week, veh, trt, trt - veh))
    print()

    print("Mean body weight (g) by group: %s"
          % ", ".join("%s %.1f" % (g, m) for g, m in
                      df.groupby("treatment_group", observed=True)["body_weight_g"].mean().items()))
    print()


def primary_mixed_model(df):
    """PRIMARY inferential analysis: random-intercept mixed model."""
    print("=" * 72)
    print("PRIMARY ANALYSIS (INFERENTIAL RESULT)")
    print("Linear mixed-effects model, random intercept for each animal")
    print("=" * 72)
    print("Model    : tumour_volume_mm3 ~ treatment_group + week")
    print("Random   : intercept by animal_id")
    print("Reference: treatment_group = %s, so the treatment coefficient is"
          % REFERENCE_GROUP)
    print("           %s minus %s in mm3." % (COMPARISON_GROUP, REFERENCE_GROUP))
    print("Sample    : 24 animals contributing 120 measurements.")
    print()

    model = smf.mixedlm(
        "tumour_volume_mm3 ~ treatment_group + week",
        data=df,
        groups=df["animal_id"],
    )
    # BFGS is used explicitly: the default L-BFGS-B path fails on this fit with a
    # singular information matrix, while BFGS, CG, Powell and Nelder-Mead all
    # converge to the same solution.
    fit = model.fit(reml=True, method="bfgs")

    print(fit.summary())
    print()

    term = "treatment_group[T.%s]" % COMPARISON_GROUP
    estimate = fit.params[term]
    std_err = fit.bse[term]
    z_stat = fit.tvalues[term]
    p_value = fit.pvalues[term]
    ci = fit.conf_int().loc[term]

    # Variance components, to show how much of the spread sits between animals.
    var_animal = float(fit.cov_re.iloc[0, 0])
    var_resid = float(fit.scale)
    icc = var_animal / (var_animal + var_resid)

    print("-" * 72)
    print("PRIMARY RESULT")
    print("-" * 72)
    print("Converged                      : %s" % fit.converged)
    print("Treatment effect (treated - vehicle) : %.2f mm3" % estimate)
    print("Standard error                 : %.2f mm3" % std_err)
    print("95%% confidence interval        : %.2f to %.2f mm3" % (ci[0], ci[1]))
    print("z statistic                    : %.3f" % z_stat)
    print("p-value                        : %s" % format_p(p_value))
    print("Week coefficient               : %.2f mm3 per week (p = %s)"
          % (fit.params["week"], format_p(fit.pvalues["week"])))
    print("Between-animal variance        : %.1f mm3^2 (SD %.1f mm3)"
          % (var_animal, np.sqrt(var_animal)))
    print("Residual variance              : %.1f mm3^2 (SD %.1f mm3)"
          % (var_resid, np.sqrt(var_resid)))
    print("Intraclass correlation         : %.3f" % icc)
    print("Sample size                    : 24 animals, 120 measurements")
    print()

    return {
        "estimate": estimate,
        "std_err": std_err,
        "z": z_stat,
        "p": p_value,
        "ci_low": ci[0],
        "ci_high": ci[1],
        "week_coef": fit.params["week"],
        "week_p": fit.pvalues["week"],
        "var_animal": var_animal,
        "var_resid": var_resid,
        "icc": icc,
        "converged": fit.converged,
    }


def secondary_final_week_ttest(df):
    """SECONDARY sensitivity check. Not the study's inferential result."""
    print("=" * 72)
    print("SECONDARY SENSITIVITY CHECK (NOT THE INFERENTIAL RESULT)")
    print("Plain two-sample comparison of final-week values, rows treated as")
    print("independent. Reported for support only.")
    print("=" * 72)

    final_week = int(df["week"].max())
    last = df[df["week"] == final_week]

    veh = last.loc[last["treatment_group"] == REFERENCE_GROUP, "tumour_volume_mm3"].to_numpy()
    trt = last.loc[last["treatment_group"] == COMPARISON_GROUP, "tumour_volume_mm3"].to_numpy()

    t_stat, p_value = stats.ttest_ind(trt, veh, equal_var=False)
    diff = trt.mean() - veh.mean()

    # Welch confidence interval for the difference in means.
    se = np.sqrt(veh.var(ddof=1) / veh.size + trt.var(ddof=1) / trt.size)
    dof = se ** 4 / (
        (veh.var(ddof=1) / veh.size) ** 2 / (veh.size - 1)
        + (trt.var(ddof=1) / trt.size) ** 2 / (trt.size - 1)
    )
    crit = stats.t.ppf(0.975, dof)
    ci_low, ci_high = diff - crit * se, diff + crit * se

    print("Week analysed                  : %d (final week only)" % final_week)
    print("Rows used                      : %d (%d %s, %d %s)"
          % (len(last), veh.size, REFERENCE_GROUP, trt.size, COMPARISON_GROUP))
    print("%-8s mean (SD)             : %.1f (%.1f) mm3"
          % (REFERENCE_GROUP, veh.mean(), veh.std(ddof=1)))
    print("%-8s mean (SD)             : %.1f (%.1f) mm3"
          % (COMPARISON_GROUP, trt.mean(), trt.std(ddof=1)))
    print("Difference (treated - vehicle) : %.2f mm3" % diff)
    print("Welch 95%% confidence interval  : %.2f to %.2f mm3" % (ci_low, ci_high))
    print("Welch t statistic              : %.3f (df %.2f)" % (t_stat, dof))
    print("p-value                        : %s" % format_p(p_value))
    print()
    print("Note: this check uses one row per animal, so the rows it treats as")
    print("independent happen to be independent, but it discards weeks 1 to 4")
    print("and does not model the growth over time. It supports the primary")
    print("model; it does not replace it.")
    print()

    return {
        "week": final_week,
        "veh_mean": veh.mean(),
        "veh_sd": veh.std(ddof=1),
        "trt_mean": trt.mean(),
        "trt_sd": trt.std(ddof=1),
        "diff": diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "t": t_stat,
        "dof": dof,
        "p": p_value,
        "n_veh": veh.size,
        "n_trt": trt.size,
    }


def format_p(p):
    """Format a p-value without pretending to more precision than is useful."""
    if p < 1e-4:
        return "%.3e" % p
    return "%.5f" % p


def main():
    df = load_data(DATA_FILE)
    describe_design(df)
    primary = primary_mixed_model(df)
    secondary = secondary_final_week_ttest(df)

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print("PRIMARY   (mixed model, 24 animals, 120 measurements):")
    print("          %s - %s = %.1f mm3, 95%% CI %.1f to %.1f, p = %s"
          % (COMPARISON_GROUP, REFERENCE_GROUP, primary["estimate"],
             primary["ci_low"], primary["ci_high"], format_p(primary["p"])))
    print("SECONDARY (week-%d two-sample check, sensitivity only, not the result):"
          % secondary["week"])
    print("          %s - %s = %.1f mm3, 95%% CI %.1f to %.1f, p = %s"
          % (COMPARISON_GROUP, REFERENCE_GROUP, secondary["diff"],
             secondary["ci_low"], secondary["ci_high"], format_p(secondary["p"])))
    print("=" * 72)


if __name__ == "__main__":
    main()
