"""Analysis of the canine elbow osteoarthritis analgesic comparison.

Design
------
24 client-owned dogs, 12 per treatment arm, each walked over a force platform
at 5 visits (baseline and weeks 2, 4, 8, 12). Outcome is peak vertical force
through the affected forelimb as a percentage of body weight (%BW).

Dependence structure
--------------------
Each dog contributes five rows. The five rows from one dog share that dog's
own weight-bearing level, so the 120 rows are NOT 120 independent
observations. The dog is the unit that was randomised, so the dog is the
independent experimental unit and the effective sample size is 24.

What this script runs
---------------------
1. PRIMARY (dependence-aware).  A linear mixed-effects model of peak vertical
   force on treatment arm, visit week, and their interaction, with a random
   intercept for each dog. The random intercept absorbs the persistent
   dog-to-dog differences, so the repeated visits within a dog are modelled as
   correlated. The treatment effect is read from this model as the
   arm difference at each visit, with week 12 as the primary readout.

2. SUPPORTING (dog level).  One week-12 value per dog, Welch two-sample t-test.
   Sample size is 24 dogs. This respects the unit of randomisation and is
   reported only as a check that the primary model's week-12 contrast does not
   depend on the mixed-model machinery.

3. SECONDARY SENSITIVITY ONLY (row level, NOT the inferential result).  A plain
   two-sample t-test over all 120 visit rows, ignoring dog identity. Its
   sample size is visits, not dogs, and it treats correlated rows as
   independent, so its standard error is too small and its p-value too
   extreme. It is printed to quantify how much pseudoreplication would
   overstate the evidence. It must never be read as the study result.

Run:  /usr/local/bin/python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "pvf_repeated_measures.csv")

OUTCOME = "peak_vertical_force_pctbw"
GROUP = "dog_id"
ARM = "treatment_arm"
WEEK = "visit_week"

REFERENCE_ARM = "established"
TEST_ARM = "new"
PRIMARY_WEEK = 12
VISIT_WEEKS = [0, 2, 4, 8, 12]


# ---------------------------------------------------------------- utilities

def rule(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def load_data():
    df = pd.read_csv(CSV_PATH)
    df[ARM] = pd.Categorical(df[ARM], categories=[REFERENCE_ARM, TEST_ARM])
    return df


def describe_design(df):
    rule("1. DESIGN AND DEPENDENCE STRUCTURE")
    n_rows = len(df)
    n_dogs = df[GROUP].nunique()
    print("Rows (visits)                     : %d" % n_rows)
    print("Independent experimental units    : %d dogs" % n_dogs)
    print("Rows per dog                      : %s"
          % sorted(df.groupby(GROUP).size().unique().tolist()))
    print("Missing values                    : %d" % int(df.isna().sum().sum()))
    print()

    per_arm = df.groupby(ARM, observed=True)[GROUP].nunique()
    print("Dogs per arm:")
    for arm, n in per_arm.items():
        print("  %-12s %d dogs" % (arm, n))
    print()

    print("Mean %s by arm and visit week (%%BW):" % OUTCOME)
    cell = df.pivot_table(index=WEEK, columns=ARM, values=OUTCOME,
                          aggfunc="mean", observed=True)
    cell["difference (new - established)"] = cell[TEST_ARM] - cell[REFERENCE_ARM]
    print(cell.round(2).to_string())
    print()
    print("Note: the %d rows are five repeated visits from each of %d dogs."
          % (n_rows, n_dogs))
    print("      Rows from the same dog are correlated and must not be treated")
    print("      as independent observations.")


# ------------------------------------------------------- 1. primary analysis

def contrast_from_names(names, wanted):
    """Build a contrast vector picking out the named coefficients."""
    vec = np.zeros(len(names))
    for name in wanted:
        vec[names.index(name)] = 1.0
    return vec


def wald(result, contrast):
    """Estimate, SE, 95% CI and two-sided Wald p for c' beta."""
    beta = np.asarray(result.fe_params)
    cov = np.asarray(result.cov_params())[:len(beta), :len(beta)]
    est = float(contrast @ beta)
    se = float(np.sqrt(contrast @ cov @ contrast))
    z = est / se
    p = 2.0 * stats.norm.sf(abs(z))
    crit = stats.norm.ppf(0.975)
    return est, se, est - crit * se, est + crit * se, z, p


def primary_mixed_model(df):
    rule("2. PRIMARY ANALYSIS (dependence-aware linear mixed-effects model)")
    print("Model : %s ~ C(%s) * C(%s),  random intercept for each %s"
          % (OUTCOME, ARM, WEEK, GROUP))
    print("Fit   : statsmodels MixedLM, REML")
    print("Reason: each dog supplies five visits. The per-dog random intercept")
    print("        represents that dog's own persistent weight-bearing level,")
    print("        which makes the five rows from one dog correlated rather")
    print("        than independent. The arm-by-week interaction lets the two")
    print("        arms start together at baseline and separate over time.")
    print()

    formula = ("%s ~ C(%s, Treatment('%s')) * C(%s)"
               % (OUTCOME, ARM, REFERENCE_ARM, WEEK))
    model = smf.mixedlm(formula, data=df, groups=df[GROUP])
    result = model.fit(reml=True, method="lbfgs")
    print(result.summary())
    print()

    var_dog = float(np.asarray(result.cov_re)[0, 0])
    var_resid = float(result.scale)
    icc = var_dog / (var_dog + var_resid)
    m = df.groupby(GROUP).size().mean()
    design_effect = 1.0 + (m - 1.0) * icc

    print("Variance components")
    print("  Between-dog variance (random intercept) : %.3f (SD %.3f %%BW)"
          % (var_dog, np.sqrt(var_dog)))
    print("  Within-dog residual variance            : %.3f (SD %.3f %%BW)"
          % (var_resid, np.sqrt(var_resid)))
    print("  Intraclass correlation (ICC)            : %.3f" % icc)
    print("  Design effect 1 + (m-1)*ICC, m = %.1f     : %.2f"
          % (m, design_effect))
    print("  -> %d rows carry about the information of %.0f independent"
          % (len(df), len(df) / design_effect))
    print("     observations. This is why the row-level test in section 4 is")
    print("     a sensitivity check only.")
    print()

    names = list(result.fe_params.index)
    arm_term = "C(%s, Treatment('%s'))[T.%s]" % (ARM, REFERENCE_ARM, TEST_ARM)

    rows = []
    for week in VISIT_WEEKS:
        wanted = [arm_term]
        if week != VISIT_WEEKS[0]:
            wanted.append("%s:C(%s)[T.%d]" % (arm_term, WEEK, week))
        est, se, lo, hi, z, p = wald(result, contrast_from_names(names, wanted))
        rows.append({"visit_week": week, "estimate_pctbw": est, "std_err": se,
                     "ci_low": lo, "ci_high": hi, "z": z, "p_value": p})
    contrasts = pd.DataFrame(rows).set_index("visit_week")

    print("Model-based treatment effect (new minus established), by visit")
    print("Positive values favour the new analgesic. 95% Wald intervals.")
    print(contrasts.round(4).to_string())
    print()

    base = contrasts.loc[0]
    print("Baseline check (week 0, before treatment):")
    print("  %+.2f %%BW (95%% CI %.2f to %.2f), p = %.4f"
          % (base["estimate_pctbw"], base["ci_low"], base["ci_high"],
             base["p_value"]))
    print("  The arms are comparable at baseline, as expected before dosing.")
    print()

    prim = contrasts.loc[PRIMARY_WEEK]
    print("PRIMARY READOUT - treatment effect at week %d:" % PRIMARY_WEEK)
    print("  %+.2f %%BW (95%% CI %.2f to %.2f), SE %.2f, z = %.2f, p = %.3g"
          % (prim["estimate_pctbw"], prim["ci_low"], prim["ci_high"],
             prim["std_err"], prim["z"], prim["p_value"]))
    print()
    print("Caveat: MixedLM Wald tests use a normal approximation. With only")
    print("        24 dogs the intervals above are mildly optimistic; the")
    print("        dog-level t-test in section 3 uses finite-sample t degrees")
    print("        of freedom and is reported alongside for that reason.")

    return result, contrasts, icc, design_effect


# ------------------------------------------------ 2. supporting check (dogs)

def supporting_dog_level(df):
    rule("3. SUPPORTING CHECK AT THE DOG LEVEL (n = dogs, not visits)")
    print("One week-%d value per dog, Welch two-sample t-test." % PRIMARY_WEEK)
    print("Sample size is %d dogs, matching the unit of randomisation."
          % df[GROUP].nunique())
    print("This is a supporting check on the primary week-%d contrast, not a"
          % PRIMARY_WEEK)
    print("replacement for the dependence-aware model.")
    print()

    wk = df[df[WEEK] == PRIMARY_WEEK]
    a = wk.loc[wk[ARM] == TEST_ARM, OUTCOME].to_numpy()
    b = wk.loc[wk[ARM] == REFERENCE_ARM, OUTCOME].to_numpy()
    t, p = stats.ttest_ind(a, b, equal_var=False)
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
    dfree = (se ** 4) / ((a.var(ddof=1) / a.size) ** 2 / (a.size - 1)
                         + (b.var(ddof=1) / b.size) ** 2 / (b.size - 1))
    crit = stats.t.ppf(0.975, dfree)

    print("  new          : n = %2d dogs, mean %.2f %%BW, SD %.2f"
          % (a.size, a.mean(), a.std(ddof=1)))
    print("  established  : n = %2d dogs, mean %.2f %%BW, SD %.2f"
          % (b.size, b.mean(), b.std(ddof=1)))
    print("  difference   : %+.2f %%BW (95%% CI %.2f to %.2f)"
          % (diff, diff - crit * se, diff + crit * se))
    print("  Welch t = %.2f, df = %.1f, p = %.3g" % (t, dfree, p))
    return {"diff": diff, "ci": (diff - crit * se, diff + crit * se),
            "t": float(t), "df": float(dfree), "p": float(p),
            "n_new": int(a.size), "n_est": int(b.size)}


# ------------------------------- 3. secondary sensitivity check (row level)

def secondary_row_level(df, design_effect):
    rule("4. SECONDARY SENSITIVITY CHECK ONLY - NOT THE INFERENTIAL RESULT")
    print("Plain two-sample t-test over ALL %d visit rows, ignoring dog_id."
          % len(df))
    print()
    print("  *** Its sample size is VISITS, not dogs. ***")
    print("  *** It treats five correlated rows from one dog as five        ***")
    print("  *** independent observations (pseudoreplication), so its       ***")
    print("  *** standard error is too small and its p-value too extreme.   ***")
    print("  *** It also pools the pre-treatment baseline visit with the    ***")
    print("  *** post-treatment visits, so it dilutes the true effect.      ***")
    print("  *** Report it as a sensitivity check only. The inferential     ***")
    print("  *** result is the mixed model in section 2.                    ***")
    print()

    a = df.loc[df[ARM] == TEST_ARM, OUTCOME].to_numpy()
    b = df.loc[df[ARM] == REFERENCE_ARM, OUTCOME].to_numpy()
    t, p = stats.ttest_ind(a, b, equal_var=False)
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)

    print("  new          : n = %3d visit rows (from %d dogs), mean %.2f %%BW"
          % (a.size, df.loc[df[ARM] == TEST_ARM, GROUP].nunique(), a.mean()))
    print("  established  : n = %3d visit rows (from %d dogs), mean %.2f %%BW"
          % (b.size, df.loc[df[ARM] == REFERENCE_ARM, GROUP].nunique(),
             b.mean()))
    print("  difference   : %+.2f %%BW, naive SE %.3f" % (diff, se))
    print("  Welch t = %.2f, p = %.3g  <-- SENSITIVITY ONLY" % (t, p))
    print()
    print("  With ICC-based design effect %.2f, the honest standard error for"
          % design_effect)
    print("  this contrast would be about %.3f, i.e. %.1fx wider than the"
          % (se * np.sqrt(design_effect), np.sqrt(design_effect)))
    print("  naive value printed above.")
    return {"diff": diff, "se": se, "t": float(t), "p": float(p),
            "n_rows_new": int(a.size), "n_rows_est": int(b.size)}


def main():
    df = load_data()
    describe_design(df)
    _, contrasts, icc, design_effect = primary_mixed_model(df)
    supporting_dog_level(df)
    secondary_row_level(df, design_effect)

    rule("5. CONCLUSION (read from the PRIMARY dependence-aware model)")
    prim = contrasts.loc[PRIMARY_WEEK]
    print("Primary estimate, week %d, new minus established:" % PRIMARY_WEEK)
    print("  %+.2f %%BW (95%% CI %.2f to %.2f), p = %.3g"
          % (prim["estimate_pctbw"], prim["ci_low"], prim["ci_high"],
             prim["p_value"]))
    print("Intraclass correlation among visits within a dog: %.3f" % icc)
    print("The inferential result is the mixed model. The row-level test in")
    print("section 4 is a sensitivity check whose n is visits, not dogs.")


if __name__ == "__main__":
    main()
