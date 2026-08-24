"""Analysis for the cognitive training reaction-time study.

Primary inference: linear mixed-effects model of reaction_time_ms on training_regime
with a random intercept for volunteer_ref. The random intercept accounts for the fact
that the twelve trials contributed by one volunteer are repeated measurements on the
same person and are not independent of one another.

Secondary (sensitivity only): a two-sample Welch t-test across all 264 individual trial
rows. That test treats trials as independent and therefore overstates the evidence; it
is reported as a sensitivity check and is not the inferential result of the study.

Run: /usr/local/bin/python3 analysis.py
"""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

DATA_FILE = "reaction_times.csv"
OUTCOME = "reaction_time_ms"
GROUP = "training_regime"
UNIT = "volunteer_ref"
TRIAL = "trial_number"

ADAPTIVE = "adaptive"
CONTROL = "active_control"


def load_data(path=DATA_FILE):
    df = pd.read_csv(path)
    expected = [UNIT, GROUP, TRIAL, OUTCOME]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError("missing expected columns: %s" % missing)
    return df


def describe(df):
    """Counts and simple summaries. No inference here."""
    lines = []
    n_rows = len(df)
    n_volunteers = df[UNIT].nunique()
    trials_per_volunteer = df.groupby(UNIT)[TRIAL].size()

    # group membership is a property of the volunteer, so take it one row per volunteer
    per_volunteer = df.groupby(UNIT).agg(
        training_regime=(GROUP, "first"),
        n_trials=(TRIAL, "size"),
        mean_rt_ms=(OUTCOME, "mean"),
    )
    volunteers_per_group = per_volunteer["training_regime"].value_counts()

    lines.append("DESIGN AND COUNTS")
    lines.append("  rows (trials) in file:            %d" % n_rows)
    lines.append("  volunteers:                       %d" % n_volunteers)
    lines.append("  trials per volunteer (min..max):  %d..%d"
                 % (trials_per_volunteer.min(), trials_per_volunteer.max()))
    for regime in (ADAPTIVE, CONTROL):
        n_vol = int(volunteers_per_group.get(regime, 0))
        n_trials = int((df[GROUP] == regime).sum())
        lines.append("  %-15s volunteers: %2d   trials: %3d" % (regime, n_vol, n_trials))
    lines.append("  missing outcome values:           %d" % int(df[OUTCOME].isna().sum()))

    lines.append("")
    lines.append("TRIAL-LEVEL SUMMARY OF %s" % OUTCOME)
    for regime in (ADAPTIVE, CONTROL):
        vals = df.loc[df[GROUP] == regime, OUTCOME]
        lines.append("  %-15s n=%3d  mean=%7.2f  sd=%6.2f  min=%6.1f  max=%6.1f"
                     % (regime, len(vals), vals.mean(), vals.std(ddof=1),
                        vals.min(), vals.max()))

    lines.append("")
    lines.append("VOLUNTEER-LEVEL SUMMARY (mean of each volunteer's twelve trials)")
    for regime in (ADAPTIVE, CONTROL):
        vals = per_volunteer.loc[per_volunteer["training_regime"] == regime, "mean_rt_ms"]
        lines.append("  %-15s n=%2d  mean=%7.2f  sd=%6.2f"
                     % (regime, len(vals), vals.mean(), vals.std(ddof=1)))

    # spread between volunteers vs. within a volunteer, purely descriptive
    between_sd = per_volunteer["mean_rt_ms"].std(ddof=1)
    within_sd = df.groupby(UNIT)[OUTCOME].std(ddof=1).mean()
    lines.append("")
    lines.append("  sd of the %d volunteer means:      %6.2f ms" % (n_volunteers, between_sd))
    lines.append("  mean within-volunteer sd:         %6.2f ms" % within_sd)

    return "\n".join(lines), per_volunteer


def primary_mixed_model(df):
    """Random-intercept model: reaction_time_ms ~ training_regime + (1 | volunteer_ref)."""
    d = df.copy()
    # make active_control the reference level so the coefficient is adaptive - active_control
    d[GROUP] = pd.Categorical(d[GROUP], categories=[CONTROL, ADAPTIVE])

    model = smf.mixedlm("%s ~ C(%s)" % (OUTCOME, GROUP), data=d, groups=d[UNIT])
    fit = model.fit(reml=True)

    term = [name for name in fit.params.index if name.startswith("C(%s)" % GROUP)][0]
    estimate = float(fit.params[term])
    se = float(fit.bse[term])
    zval = float(fit.tvalues[term])
    pval = float(fit.pvalues[term])
    ci = fit.conf_int().loc[term]
    lo, hi = float(ci[0]), float(ci[1])

    # variance components
    var_volunteer = float(fit.cov_re.iloc[0, 0])
    var_resid = float(fit.scale)
    icc = var_volunteer / (var_volunteer + var_resid)

    lines = []
    lines.append("PRIMARY ANALYSIS")
    lines.append("  linear mixed-effects model, REML")
    lines.append("  %s ~ %s + (1 | %s)" % (OUTCOME, GROUP, UNIT))
    lines.append("  reference level: %s" % CONTROL)
    lines.append("")
    lines.append("  fixed effect (%s - %s)" % (ADAPTIVE, CONTROL))
    lines.append("    estimate:      %8.2f ms" % estimate)
    lines.append("    std. error:    %8.2f ms" % se)
    lines.append("    z:             %8.3f" % zval)
    lines.append("    p (Wald):      %8.4f" % pval)
    lines.append("    95%% CI:        %8.2f to %.2f ms" % (lo, hi))
    lines.append("")
    lines.append("  intercept (%s mean):  %7.2f ms" % (CONTROL, float(fit.params["Intercept"])))
    lines.append("  variance components")
    lines.append("    between volunteers:  %8.2f  (sd %6.2f ms)"
                 % (var_volunteer, np.sqrt(var_volunteer)))
    lines.append("    residual (within):   %8.2f  (sd %6.2f ms)"
                 % (var_resid, np.sqrt(var_resid)))
    lines.append("    intraclass correlation: %6.3f" % icc)

    result = dict(estimate=estimate, se=se, z=zval, p=pval, lo=lo, hi=hi,
                  var_volunteer=var_volunteer, var_resid=var_resid, icc=icc,
                  intercept=float(fit.params["Intercept"]))
    return "\n".join(lines), result, fit


def secondary_naive_ttest(df):
    """SENSITIVITY CHECK ONLY. Treats all 264 trial rows as independent, which they are not."""
    a = df.loc[df[GROUP] == ADAPTIVE, OUTCOME]
    c = df.loc[df[GROUP] == CONTROL, OUTCOME]
    tstat, pval = stats.ttest_ind(a, c, equal_var=False)
    diff = float(a.mean() - c.mean())

    # Welch standard error and df, for the confidence interval
    se = float(np.sqrt(a.var(ddof=1) / len(a) + c.var(ddof=1) / len(c)))
    dof = se ** 4 / ((a.var(ddof=1) / len(a)) ** 2 / (len(a) - 1)
                     + (c.var(ddof=1) / len(c)) ** 2 / (len(c) - 1))
    crit = stats.t.ppf(0.975, dof)

    lines = []
    lines.append("SECONDARY SENSITIVITY CHECK (NOT the reported inferential result)")
    lines.append("  Welch two-sample t-test on all %d individual trial rows." % len(df))
    lines.append("  This test treats the twelve trials of a volunteer as independent")
    lines.append("  observations. They are not, so this p-value overstates the evidence.")
    lines.append("    mean difference (%s - %s): %7.2f ms" % (ADAPTIVE, CONTROL, diff))
    lines.append("    std. error:  %8.2f ms" % se)
    lines.append("    t:           %8.3f" % float(tstat))
    lines.append("    df (Welch):  %8.2f" % float(dof))
    lines.append("    p:           %8.6f" % float(pval))
    lines.append("    95%% CI:      %8.2f to %.2f ms"
                 % (diff - crit * se, diff + crit * se))

    result = dict(diff=diff, se=se, t=float(tstat), df=float(dof), p=float(pval),
                  lo=diff - crit * se, hi=diff + crit * se)
    return "\n".join(lines), result


def main():
    df = load_data()

    desc_text, per_volunteer = describe(df)
    primary_text, primary, _fit = primary_mixed_model(df)
    secondary_text, secondary = secondary_naive_ttest(df)

    print(desc_text)
    print()
    print(primary_text)
    print()
    print(secondary_text)
    print()
    print("COMPARISON OF THE TWO STANDARD ERRORS")
    print("  primary (random intercept for volunteer): %6.2f ms, p = %.4f"
          % (primary["se"], primary["p"]))
    print("  secondary (trials pooled as independent): %6.2f ms, p = %.6f"
          % (secondary["se"], secondary["p"]))
    print("  The conclusion of the study is the primary model result.")


if __name__ == "__main__":
    main()
