"""Shelter-cat enrichment study: dependence-aware comparison of faecal
glucocorticoid metabolite (FGM) concentration between husbandry groups.

One row of shelter_cat_fgm.csv is one cat on one morning. Each cat contributes
six rows, so the 144 rows are repeated measures on 24 independent animals.
The primary inference is therefore a linear mixed model with a per-cat random
intercept. A row-level two-sample t-test is reported only as a clearly labelled
secondary sensitivity check.
"""

import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "shelter_cat_fgm.csv")

OUTCOME = "fgm_ng_per_g"
GROUP_COL = "husbandry_group"
UNIT_COL = "cat_ref"
REFERENCE_LEVEL = "usual_husbandry"  # control arm is the model reference


def load_data(path):
    df = pd.read_csv(path)
    df[GROUP_COL] = pd.Categorical(
        df[GROUP_COL], categories=[REFERENCE_LEVEL, "enrichment"], ordered=False
    )
    return df


def describe(df):
    print("=" * 72)
    print("DATA")
    print("=" * 72)
    print(f"File: {os.path.basename(DATA_FILE)}")
    print(f"Columns: {', '.join(df.columns)}")
    print("One row = one cat on one morning (one faecal sample + that "
          "morning's food record).")
    n_rows = len(df)
    n_cats = df[UNIT_COL].nunique()
    print(f"Rows (samples): {n_rows}")
    print(f"Cats (independent units): {n_cats}")
    rows_per_cat = df.groupby(UNIT_COL, observed=True).size()
    print(f"Rows per cat: min {rows_per_cat.min()}, max {rows_per_cat.max()}")
    print()

    summary = (
        df.groupby(GROUP_COL, observed=True)
        .agg(cats=(UNIT_COL, "nunique"),
             rows=(OUTCOME, "size"),
             mean_fgm=(OUTCOME, "mean"),
             sd_fgm=(OUTCOME, "std"),
             min_fgm=(OUTCOME, "min"),
             max_fgm=(OUTCOME, "max"),
             mean_food=("food_intake_pct", "mean"))
    )
    print("Per-group summary (row level):")
    print(summary.round(2).to_string())
    print()

    cat_means = (df.groupby([UNIT_COL, GROUP_COL], observed=True)[OUTCOME]
                 .mean().reset_index())
    print("Per-cat mean FGM, summarised by group:")
    print(cat_means.groupby(GROUP_COL, observed=True)[OUTCOME]
          .agg(["count", "mean", "std", "min", "max"]).round(2).to_string())
    print()

    within_sd = df.groupby(UNIT_COL, observed=True)[OUTCOME].std()
    print(f"Median within-cat SD of FGM: {within_sd.median():.2f} ng/g")
    print(f"Between-cat SD of per-cat mean FGM (all cats): "
          f"{cat_means[OUTCOME].std():.2f} ng/g")
    print()
    return cat_means


def primary_mixed_model(df):
    print("=" * 72)
    print("PRIMARY ANALYSIS (inferential result)")
    print("=" * 72)
    print("Linear mixed model: fgm_ng_per_g ~ husbandry_group,")
    print("random intercept for each cat (groups = cat_ref), REML.")
    print(f"Reference level: {REFERENCE_LEVEL}")
    print()

    model = smf.mixedlm(f"{OUTCOME} ~ {GROUP_COL}", df, groups=df[UNIT_COL])
    fit = model.fit(reml=True)
    print(fit.summary())
    print()

    term = [t for t in fit.params.index if t.startswith(GROUP_COL)][0]
    est = fit.params[term]
    se = fit.bse[term]
    zval = fit.tvalues[term]
    pval = fit.pvalues[term]
    ci_low, ci_high = fit.conf_int().loc[term]

    # Variance components and the intraclass correlation they imply.
    var_cat = float(fit.cov_re.iloc[0, 0])
    var_resid = float(fit.scale)
    icc = var_cat / (var_cat + var_resid)

    print("-" * 72)
    print("Headline group contrast (enrichment minus usual husbandry):")
    print(f"  estimate      : {est:.2f} ng/g")
    print(f"  standard error: {se:.2f} ng/g")
    print(f"  95% CI        : {ci_low:.2f} to {ci_high:.2f} ng/g")
    print(f"  z             : {zval:.3f}")
    print(f"  p             : {pval:.3g}")
    print()
    print("Variance components:")
    print(f"  between-cat variance (random intercept): {var_cat:.2f} "
          f"(SD {np.sqrt(var_cat):.2f} ng/g)")
    print(f"  residual within-cat variance           : {var_resid:.2f} "
          f"(SD {np.sqrt(var_resid):.2f} ng/g)")
    print(f"  intraclass correlation (ICC)           : {icc:.3f}")
    print(f"Cats: {df[UNIT_COL].nunique()}   Samples: {len(df)}")
    print("-" * 72)
    print()
    return {"estimate": est, "se": se, "ci_low": ci_low, "ci_high": ci_high,
            "z": zval, "p": pval, "var_cat": var_cat, "var_resid": var_resid,
            "icc": icc}


def secondary_row_level_test(df, icc):
    print("=" * 72)
    print("SECONDARY SENSITIVITY CHECK (NOT the inferential result)")
    print("=" * 72)
    print("Plain two-sample Welch t-test on all 144 rows, treating every row")
    print("as if it were an independent observation. This assumption is FALSE")
    print("for these data: the six rows from one cat are repeated measures on")
    print("the same animal.")
    print()

    a = df.loc[df[GROUP_COL] == "enrichment", OUTCOME]
    b = df.loc[df[GROUP_COL] == REFERENCE_LEVEL, OUTCOME]
    tstat, pval = stats.ttest_ind(a, b, equal_var=False)
    diff = a.mean() - b.mean()
    se_diff = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    dfree = (se_diff ** 4) / (
        (a.var(ddof=1) / len(a)) ** 2 / (len(a) - 1)
        + (b.var(ddof=1) / len(b)) ** 2 / (len(b) - 1)
    )
    crit = stats.t.ppf(0.975, dfree)

    print(f"  n rows        : {len(a)} enrichment vs {len(b)} usual husbandry")
    print(f"  mean difference: {diff:.2f} ng/g")
    print(f"  standard error : {se_diff:.2f} ng/g")
    print(f"  95% CI         : {diff - crit * se_diff:.2f} to "
          f"{diff + crit * se_diff:.2f} ng/g")
    print(f"  t              : {tstat:.3f}   df {dfree:.1f}")
    print(f"  p              : {pval:.3g}")
    print()

    # Design effect for a balanced cluster design: 1 + (m - 1) * ICC.
    m = len(df) / df[UNIT_COL].nunique()
    deff = 1 + (m - 1) * icc
    print("Why this p-value is optimistic:")
    print(f"  Each cat gives {m:.0f} correlated samples with ICC {icc:.3f}.")
    print(f"  Design effect 1 + (m-1)*ICC = {deff:.2f}, so the 144 rows carry")
    print(f"  about {len(df) / deff:.1f} rows' worth of independent")
    print("  information, close to the 24 cats actually randomised. The")
    print("  row-level test therefore understates the standard error and")
    print("  overstates the significance. Use the mixed model above.")
    print()
    return {"diff": diff, "se": se_diff, "t": tstat, "p": pval, "deff": deff}


def cat_level_crosscheck(cat_means):
    """Same contrast on the 24 cat means: 24 genuinely independent numbers."""
    print("=" * 72)
    print("CROSS-CHECK: t-test on the 24 per-cat means")
    print("=" * 72)
    a = cat_means.loc[cat_means[GROUP_COL] == "enrichment", OUTCOME]
    b = cat_means.loc[cat_means[GROUP_COL] == REFERENCE_LEVEL, OUTCOME]
    tstat, pval = stats.ttest_ind(a, b, equal_var=False)
    diff = a.mean() - b.mean()
    se_diff = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    print(f"  n cats         : {len(a)} vs {len(b)}")
    print(f"  mean difference: {diff:.2f} ng/g")
    print(f"  standard error : {se_diff:.2f} ng/g")
    print(f"  t              : {tstat:.3f}   p: {pval:.3g}")
    print("  This collapses each cat to one number, so it respects the cat as")
    print("  the independent unit and should agree with the mixed model.")
    print()


def main():
    df = load_data(DATA_FILE)
    cat_means = describe(df)
    primary = primary_mixed_model(df)
    secondary_row_level_test(df, primary["icc"])
    cat_level_crosscheck(cat_means)

    print("=" * 72)
    print("CONCLUSION")
    print("=" * 72)
    print(f"Primary (mixed model, {df[UNIT_COL].nunique()} cats, {len(df)} "
          "samples): enrichment changes FGM by")
    print(f"{primary['estimate']:.1f} ng/g "
          f"(95% CI {primary['ci_low']:.1f} to {primary['ci_high']:.1f}, "
          f"p = {primary['p']:.3g}).")
    print("The row-level t-test is a sensitivity check only.")


if __name__ == "__main__":
    main()
