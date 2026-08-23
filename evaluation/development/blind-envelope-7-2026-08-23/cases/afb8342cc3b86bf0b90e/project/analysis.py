"""Street tree sap flow by planting pit design.

Primary inference: linear mixed-effects model of mean daily sap flow on
planting pit design with a random intercept for each tree, which respects the
fact that the six monthly readings from one tree are repeated measures on the
same independent unit.

Secondary: a plain independent two-sample t-test across all 120 rows, reported
only as a sensitivity check. It ignores the repeated-measures structure and is
not the study's inferential result.

Run:  python3 analysis.py
"""

import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

CSV = "sap_flow.csv"
OUTCOME = "mean_daily_sap_flow_l_per_day"
GROUP = "pit_design"
UNIT = "tree_id"

REFERENCE = "conventional"
TREATMENT = "structural_soil"


def load():
    df = pd.read_csv(CSV)
    # Order the two pit designs so the model contrast is
    # structural_soil - conventional.
    df[GROUP] = pd.Categorical(df[GROUP], categories=[REFERENCE, TREATMENT])
    return df


def describe(df):
    print("=" * 70)
    print("DESIGN AND SAMPLE SIZE")
    print("=" * 70)
    n_rows = len(df)
    n_trees = df[UNIT].nunique()
    print(f"Monthly observations (rows): {n_rows}")
    print(f"Independent units (trees):   {n_trees}")
    print(f"Months per tree:             {n_rows // n_trees}")
    print()

    per_group = df.groupby(GROUP, observed=True).agg(
        trees=(UNIT, "nunique"),
        rows=(OUTCOME, "size"),
        mean_l_per_day=(OUTCOME, "mean"),
        sd_l_per_day=(OUTCOME, "std"),
    )
    print("Row-level summary by planting pit design:")
    print(per_group.round(3).to_string())
    print()

    # Tree means: one number per independent unit.
    tree_means = (
        df.groupby([UNIT, GROUP], observed=True)[OUTCOME].mean().reset_index()
    )
    print("Tree-level summary (each tree contributes one mean):")
    print(
        tree_means.groupby(GROUP, observed=True)[OUTCOME]
        .agg(["count", "mean", "std"])
        .round(3)
        .to_string()
    )
    print()
    return n_rows, n_trees, tree_means


def primary_mixed_model(df):
    print("=" * 70)
    print("PRIMARY ANALYSIS: linear mixed-effects model, random intercept per tree")
    print("=" * 70)
    print(f"Model: {OUTCOME} ~ {GROUP},  random intercept grouped by {UNIT}")
    print()

    model = smf.mixedlm(
        f"{OUTCOME} ~ {GROUP}", data=df, groups=df[UNIT]
    )
    fit = model.fit(reml=True, method="lbfgs")
    print(fit.summary())
    print()

    term = f"{GROUP}[T.{TREATMENT}]"
    estimate = fit.params[term]
    se = fit.bse[term]
    z_stat = fit.tvalues[term]
    p_value = fit.pvalues[term]
    ci_low, ci_high = fit.conf_int().loc[term]

    tree_var = float(fit.cov_re.iloc[0, 0])
    resid_var = float(fit.scale)
    icc = tree_var / (tree_var + resid_var)

    print("-" * 70)
    print("PRIMARY RESULT (this is the study's inferential result)")
    print("-" * 70)
    print(f"Treatment effect ({TREATMENT} - {REFERENCE}):")
    print(f"  estimate      = {estimate:.3f} L/day")
    print(f"  standard error= {se:.3f} L/day")
    print(f"  95% CI        = [{ci_low:.3f}, {ci_high:.3f}] L/day")
    print(f"  z statistic   = {z_stat:.3f}")
    print(f"  p-value       = {p_value:.6g}")
    print()
    print(f"  between-tree variance (random intercept) = {tree_var:.3f} (SD {tree_var ** 0.5:.3f} L/day)")
    print(f"  residual (within-tree) variance          = {resid_var:.3f} (SD {resid_var ** 0.5:.3f} L/day)")
    print(f"  intraclass correlation (ICC)             = {icc:.3f}")
    print()
    return {
        "estimate": estimate,
        "se": se,
        "z": z_stat,
        "p": p_value,
        "ci": (ci_low, ci_high),
        "tree_sd": tree_var ** 0.5,
        "resid_sd": resid_var ** 0.5,
        "icc": icc,
    }


def secondary_sensitivity_ttest(df):
    print("=" * 70)
    print("SECONDARY SENSITIVITY CHECK ONLY -- NOT THE STUDY'S FINDING")
    print("=" * 70)
    print("Plain independent two-sample t-test across all 120 rows.")
    print("This test treats the six monthly readings from a tree as six")
    print("independent observations, which they are not. It is reported only")
    print("as a sensitivity comparison against the primary mixed model above.")
    print()

    a = df.loc[df[GROUP] == REFERENCE, OUTCOME]
    b = df.loc[df[GROUP] == TREATMENT, OUTCOME]
    t_stat, p_value = stats.ttest_ind(b, a, equal_var=True)
    diff = b.mean() - a.mean()

    print(f"  raw mean difference ({TREATMENT} - {REFERENCE}) = {diff:.3f} L/day")
    print(f"  t statistic = {t_stat:.3f}")
    print(f"  df          = {len(a) + len(b) - 2}")
    print(f"  p-value     = {p_value:.6g}")
    print()
    print("  Reminder: SECONDARY SENSITIVITY CHECK ONLY. The nominal degrees of")
    print("  freedom above (118) overstate the information in the data, which")
    print("  comes from 20 trees, not 120 independent readings.")
    print()
    return {"diff": diff, "t": t_stat, "df": len(a) + len(b) - 2, "p": p_value}


def main():
    df = load()
    n_rows, n_trees, _ = describe(df)
    primary = primary_mixed_model(df)
    secondary = secondary_sensitivity_ttest(df)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"n = {n_trees} trees ({n_rows} monthly observations)")
    print(
        "PRIMARY (mixed model, random intercept per tree): "
        f"{primary['estimate']:.2f} L/day, SE {primary['se']:.2f}, "
        f"z = {primary['z']:.2f}, p = {primary['p']:.4g}"
    )
    print(
        "SECONDARY SENSITIVITY CHECK ONLY (row-level t-test): "
        f"{secondary['diff']:.2f} L/day, t({secondary['df']}) = {secondary['t']:.2f}, "
        f"p = {secondary['p']:.4g}"
    )


if __name__ == "__main__":
    main()
