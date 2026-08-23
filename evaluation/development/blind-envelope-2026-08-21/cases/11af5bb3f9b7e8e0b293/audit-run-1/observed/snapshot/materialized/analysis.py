"""
Acropora millepora thermal-stress experiment: does sustained +2 C warming
reduce net calcification?

Design note that drives everything below: thermal regime was assigned to a
whole parent colony, and the five nubbins cut from a colony are clones of one
another. So the 70 rows in nubbin_calcification.csv are 70 measurements of only
14 independent experimental units. The script therefore runs:

  1. PRIMARY   - linear mixed-effects model, random intercept per parent colony
  2. SUPPORT   - t-test on the 14 colony-level means (7 vs 7)
  3. SENSITIVITY ONLY - t-test on the 70 raw nubbin rows, shown purely to
                 illustrate the inflation that follows from pretending clonal
                 nubbins are independent. Not a result of the study.
"""

import pandas as pd
import scipy.stats as stats
import statsmodels.formula.api as smf

CSV = "nubbin_calcification.csv"


def main() -> None:
    df = pd.read_csv(CSV)

    # Make "ambient" the reference level so the fitted thermal_regime term is
    # the heated-minus-ambient contrast.
    df["thermal_regime"] = pd.Categorical(
        df["thermal_regime"], categories=["ambient", "heated"], ordered=False
    )

    print("=" * 72)
    print("DATA AS READ")
    print("=" * 72)
    print(f"Nubbin rows (measurements):      {len(df)}")
    print(f"Parent colonies (indep. units):  {df['parent_colony'].nunique()}")
    print("Colonies per regime:")
    print(
        df.groupby("thermal_regime", observed=True)["parent_colony"]
        .nunique()
        .to_string()
    )
    print("Nubbin rows per regime:")
    print(df["thermal_regime"].value_counts().sort_index().to_string())
    print()
    print("Nubbin-level mean calcification_rate by regime (descriptive only):")
    print(
        df.groupby("thermal_regime", observed=True)["calcification_rate"]
        .agg(["count", "mean", "std"])
        .round(4)
        .to_string()
    )
    print()

    # ------------------------------------------------------------------
    # 1. PRIMARY ANALYSIS - linear mixed-effects model.
    #    Fixed effect: thermal_regime. Random intercept: parent_colony.
    #    The random intercept absorbs the shared-genotype baseline, so the
    #    treatment contrast is tested against colony-level variation rather
    #    than against within-colony nubbin noise. This is the inferential
    #    result of the study.
    # ------------------------------------------------------------------
    print("=" * 72)
    print("1. PRIMARY ANALYSIS: linear mixed-effects model")
    print("   calcification_rate ~ thermal_regime + (1 | parent_colony)")
    print("   70 nubbin rows nested in 14 parent colonies")
    print("=" * 72)
    mixed = smf.mixedlm(
        "calcification_rate ~ thermal_regime",
        data=df,
        groups=df["parent_colony"],
    )
    fit = mixed.fit(reml=True)
    print(fit.summary())
    print()

    term = "thermal_regime[T.heated]"
    est = fit.params[term]
    se = fit.bse[term]
    pval = fit.pvalues[term]
    ci_low, ci_high = fit.conf_int().loc[term]
    print("Fixed effect for the heated regime (heated minus ambient):")
    print(f"  estimate        = {est:.4f} mg CaCO3 g^-1 day^-1")
    print(f"  standard error  = {se:.4f}")
    print(f"  z              = {fit.tvalues[term]:.4f}")
    print(f"  p-value         = {pval:.4f}")
    print(f"  95% CI          = [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"  colony random-intercept variance = {fit.cov_re.iloc[0, 0]:.5f}")
    print(f"  residual (within-colony) variance = {fit.scale:.5f}")
    print()

    # ------------------------------------------------------------------
    # 2. SUPPORTING CHECK - collapse each parent colony to its own mean, then
    #    compare the 14 colony means, 7 ambient against 7 heated. One number
    #    per independent unit, so the degrees of freedom are honest.
    # ------------------------------------------------------------------
    print("=" * 72)
    print("2. SUPPORTING CHECK: t-test on the 14 colony-level means (7 vs 7)")
    print("=" * 72)
    colony_means = (
        df.groupby(["parent_colony", "thermal_regime"], observed=True)[
            "calcification_rate"
        ]
        .mean()
        .reset_index()
    )
    print("Colony means entering this test:")
    print(colony_means.round(4).to_string(index=False))
    print()

    amb_col = colony_means.loc[
        colony_means["thermal_regime"] == "ambient", "calcification_rate"
    ]
    het_col = colony_means.loc[
        colony_means["thermal_regime"] == "heated", "calcification_rate"
    ]
    t_col, p_col = stats.ttest_ind(het_col, amb_col)
    print(f"  n ambient colonies = {len(amb_col)}, mean = {amb_col.mean():.4f}, sd = {amb_col.std(ddof=1):.4f}")
    print(f"  n heated  colonies = {len(het_col)}, mean = {het_col.mean():.4f}, sd = {het_col.std(ddof=1):.4f}")
    print(f"  difference (heated - ambient) = {het_col.mean() - amb_col.mean():.4f}")
    print(f"  t = {t_col:.4f}, df = {len(amb_col) + len(het_col) - 2}, p = {p_col:.4f}")
    print()

    # ------------------------------------------------------------------
    # 3. SENSITIVITY ILLUSTRATION ONLY - NOT THE STUDY'S RESULT.
    #    Treats all 70 nubbins as independent observations. They are not:
    #    nubbins from one colony are clones and share a genotype baseline,
    #    and regime was never assigned at the nubbin level. This test claims
    #    68 degrees of freedom when only 12 are earned, so its p-value is
    #    anticonservative. Reported here solely to show the size of that
    #    distortion.
    # ------------------------------------------------------------------
    print("=" * 72)
    print("3. SENSITIVITY ILLUSTRATION ONLY - NOT THE STUDY'S RESULT")
    print("   t-test on all 70 individual nubbin rows.")
    print("   This IGNORES the shared-genotype structure: the five nubbins of a")
    print("   colony are clones, and thermal regime was assigned to colonies,")
    print("   not to nubbins. It therefore OVERSTATES the degrees of freedom")
    print("   (68 claimed vs 12 earned) and yields an anticonservative p-value.")
    print("   Shown only to illustrate what happens when nubbins are treated as")
    print("   independent. It is NOT the basis of any conclusion.")
    print("=" * 72)
    amb_row = df.loc[df["thermal_regime"] == "ambient", "calcification_rate"]
    het_row = df.loc[df["thermal_regime"] == "heated", "calcification_rate"]
    t_row, p_row = stats.ttest_ind(het_row, amb_row)
    print(f"  n ambient nubbins = {len(amb_row)}, mean = {amb_row.mean():.4f}, sd = {amb_row.std(ddof=1):.4f}")
    print(f"  n heated  nubbins = {len(het_row)}, mean = {het_row.mean():.4f}, sd = {het_row.std(ddof=1):.4f}")
    print(f"  t = {t_row:.4f}, df = {len(amb_row) + len(het_row) - 2}, p = {p_row:.4f}")
    print("  (pseudoreplicated - do not cite this p-value)")
    print()

    print("=" * 72)
    print("SUMMARY OF WHAT ENTERED WHAT")
    print("=" * 72)
    print(f"  Primary mixed model : 70 nubbin rows, 14 colony groups -> p = {pval:.4f}")
    print(f"  Supporting t-test   : 14 colony means (7 vs 7)         -> p = {p_col:.4f}")
    print(f"  Sensitivity only    : 70 nubbin rows as independent    -> p = {p_row:.4f}  [ILLUSTRATION, NOT A RESULT]")
    print("  Study sample size   : N = 14 parent colonies.")


if __name__ == "__main__":
    main()
