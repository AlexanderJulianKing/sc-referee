"""
Leaf-cutter ant forager loads: does chronic sublethal fungicide exposure reduce
the fresh mass of the leaf fragments that foragers carry?

Data:      forager_loads.csv, one row per intercepted forager,
           10 foragers per colony, 16 colonies, 160 rows.
Design:    The colony is the experimental unit. The fungicide was delivered
           through each colony's forage supply, so every worker in a colony
           shares the same exposure, the same queen, and the same fungus
           garden. Foragers are nested within colonies. The treatment was
           applied 16 times, not 160 times.

PRIMARY analysis
    Linear mixed-effects model of fragment_mass_mg on exposure_group with a
    random intercept for colony_id, fitted by REML. This respects the
    nesting: between-colony variance is estimated separately from
    within-colony (forager-to-forager) variance. This is the inferential
    result of the project.

SECONDARY sensitivity analysis
    A plain independent two-sample t-test on the 160 individual forager rows
    that ignores colony membership. It is printed only to show what ignoring
    the nesting does to the standard error. It is NOT the basis for any
    conclusion.

Run with:  /usr/local/bin/python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf

CSV_PATH = Path(__file__).resolve().parent / "forager_loads.csv"
ALPHA = 0.05
N_COLONIES_EXPECTED = 16
FORAGERS_PER_COLONY = 10


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data(path):
    """Read the forager-level CSV and check the design is what we expect."""
    df = pd.read_csv(path)

    expected_cols = [
        "colony_id",
        "exposure_group",
        "forager_id",
        "head_width_mm",
        "interception_hour",
        "fragment_mass_mg",
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing expected column(s): {missing}")
    if df[expected_cols].isna().any().any():
        raise ValueError("CSV contains missing values.")
    if df.duplicated(["colony_id", "forager_id"]).any():
        raise ValueError("Duplicate (colony_id, forager_id) pairs found.")
    if (df["fragment_mass_mg"] <= 0).any():
        raise ValueError("Non-positive fragment mass found.")

    # Exposure must be a colony-level property: exactly one label per colony.
    labels_per_colony = df.groupby("colony_id")["exposure_group"].nunique()
    if (labels_per_colony != 1).any():
        raise ValueError(
            "exposure_group varies within at least one colony; treatment was "
            "assigned to colonies, so this would break the design."
        )

    # 'exposed' = 1, 'control' = 0, so the model slope is exposed - control.
    df["exposed"] = (df["exposure_group"] == "exposed").astype(int)
    return df


def describe_design(df):
    """Print the counts that define the design, and simple group summaries."""
    colonies = df.groupby("colony_id").agg(
        exposure_group=("exposure_group", "first"),
        n_foragers=("fragment_mass_mg", "size"),
        colony_mean_mass_mg=("fragment_mass_mg", "mean"),
    )

    print("=" * 78)
    print("DESIGN AND DATA")
    print("=" * 78)
    print(f"Rows (weighed foragers)          : {len(df)}")
    print(f"Colonies (experimental units)    : {df['colony_id'].nunique()}")
    print(f"Foragers per colony              : "
          f"{colonies['n_foragers'].min()}-{colonies['n_foragers'].max()}")
    print(f"Colonies per group               : "
          f"{colonies.groupby('exposure_group').size().to_dict()}")
    print("The treatment was applied 16 times (once per colony), not 160 "
          "times.")
    print()

    print("Forager-level fragment mass (mg) by group (160 rows):")
    print(df.groupby("exposure_group")["fragment_mass_mg"]
            .agg(["size", "mean", "std", "min", "max"]).round(3).to_string())
    print()
    print("Colony-level mean fragment mass (mg) by group "
          "(the 16 independent units):")
    print(colonies.groupby("exposure_group")["colony_mean_mass_mg"]
                  .agg(["size", "mean", "std", "min", "max"])
                  .round(3).to_string())
    print()
    return colonies


# ---------------------------------------------------------------------------
# Primary analysis
# ---------------------------------------------------------------------------

def balanced_reml_check(df):
    """
    Closed-form REML/ANOVA estimates for this balanced random-intercept design.

    With equal group sizes (10 foragers in each of 16 colonies) the REML
    variance components have an exact closed form, so this is an independent
    check that the numerical optimiser landed on the right answer rather than
    stopping early. An optimiser that disagrees with these numbers has not
    converged, whatever its convergence flag says.
    """
    n = FORAGERS_PER_COLONY
    colony = (df.groupby(["colony_id", "exposure_group"])["fragment_mass_mg"]
                .mean().reset_index())
    group_mean = colony.groupby("exposure_group")["fragment_mass_mg"].transform(
        "mean"
    )

    df_colony = len(colony) - colony["exposure_group"].nunique()   # 16 - 2 = 14
    ms_colony = n * ((colony["fragment_mass_mg"] - group_mean) ** 2).sum() \
        / df_colony

    merged = df.merge(
        colony.rename(columns={"fragment_mass_mg": "colony_mean"})
              [["colony_id", "colony_mean"]],
        on="colony_id",
    )
    df_resid = len(df) - len(colony)                               # 160-16 = 144
    ms_within = ((merged["fragment_mass_mg"] - merged["colony_mean"]) ** 2) \
        .sum() / df_resid

    var_within = ms_within
    var_between = max((ms_colony - ms_within) / n, 0.0)

    mean_exposed = colony.loc[colony["exposure_group"] == "exposed",
                              "fragment_mass_mg"].mean()
    mean_control = colony.loc[colony["exposure_group"] == "control",
                              "fragment_mass_mg"].mean()
    diff = mean_exposed - mean_control
    n_exp = (colony["exposure_group"] == "exposed").sum()
    n_ctl = (colony["exposure_group"] == "control").sum()
    se = np.sqrt(ms_colony * (1 / n_exp + 1 / n_ctl) / n)
    tstat = diff / se
    pval = 2 * st.t.sf(abs(tstat), df_colony)

    return {
        "var_between": float(var_between),
        "var_within": float(var_within),
        "effect": float(diff),
        "se": float(se),
        "t": float(tstat),
        "df": int(df_colony),
        "p": float(pval),
    }


def primary_mixed_model(df, check):
    """Random-intercept model: mass ~ exposure, with colony as random effect."""
    print("=" * 78)
    print("PRIMARY ANALYSIS - LINEAR MIXED-EFFECTS MODEL (colony random "
          "effect)")
    print("=" * 78)
    print("Model : fragment_mass_mg ~ exposed, random intercept for colony_id")
    print("Fit   : statsmodels MixedLM, restricted maximum likelihood (REML)")
    print("Note  : the colony is the experimental unit; foragers are nested")
    print("        within colonies, so colony enters as a random effect and")
    print("        between-colony variance is estimated separately from")
    print("        within-colony variance.")
    print()

    model = smf.mixedlm(
        "fragment_mass_mg ~ exposed", data=df, groups=df["colony_id"]
    )
    fit = model.fit(reml=True)          # default optimiser sequence

    print(fit.summary())
    print()

    effect = float(fit.params["exposed"])
    se = float(fit.bse["exposed"])
    pval = float(fit.pvalues["exposed"])
    ci = fit.conf_int(alpha=ALPHA).loc["exposed"]
    ci_low, ci_high = float(ci.iloc[0]), float(ci.iloc[1])
    zval = float(fit.tvalues["exposed"])
    var_between = float(np.asarray(fit.cov_re)[0, 0])   # colony variance
    var_within = float(fit.scale)                       # residual (forager)
    icc = var_between / (var_between + var_within)
    control_mean = float(fit.params["Intercept"])

    # Small-sample version of the same test. MixedLM reports a Wald z test,
    # which assumes an effectively infinite number of clusters. There are 16
    # colonies, so the honest small-sample reference is a t distribution with
    # 16 - 2 = 14 degrees of freedom on the same statistic.
    df_small = check["df"]
    p_small = 2 * st.t.sf(abs(zval), df_small)
    tcrit = st.t.ppf(1 - ALPHA / 2, df_small)
    ci_low_t, ci_high_t = effect - tcrit * se, effect + tcrit * se

    print("-" * 78)
    print("PRIMARY RESULT - exposure effect (exposed minus control)")
    print("-" * 78)
    print(f"Model-estimated control mean     : {control_mean:8.3f} mg")
    print(f"Estimated exposure effect        : {effect:8.3f} mg")
    print(f"Standard error                   : {se:8.3f} mg")
    print(f"95% confidence interval (Wald z) : "
          f"[{ci_low:.3f}, {ci_high:.3f}] mg")
    print(f"Wald z statistic                 : {zval:8.3f}")
    print(f"p-value (Wald z, two-sided)      : {pval:.5f}")
    print()
    print(f"Small-sample reference with only {N_COLONIES_EXPECTED} colonies "
          f"(t on {df_small} df, same statistic):")
    print(f"  95% confidence interval        : "
          f"[{ci_low_t:.3f}, {ci_high_t:.3f}] mg")
    print(f"  p-value                        : {p_small:.5f}")
    print("  The Wald z test above assumes many clusters; with 16 colonies it")
    print("  is mildly anti-conservative. Both versions are reported so the")
    print("  conclusion does not depend on which one is used.")
    print()
    print("Variance components:")
    print(f"  Between-colony variance        : {var_between:8.3f} mg^2 "
          f"(SD {np.sqrt(var_between):.3f} mg)")
    print(f"  Within-colony variance         : {var_within:8.3f} mg^2 "
          f"(SD {np.sqrt(var_within):.3f} mg)")
    print(f"  Intraclass correlation         : {icc:8.3f} "
          f"(share of total variance that is between colonies)")
    print()

    # Independent closed-form check on the balanced design.
    print("Convergence check against the closed-form balanced REML solution:")
    print(f"  between-colony variance : model {var_between:8.3f} | "
          f"closed form {check['var_between']:8.3f} mg^2")
    print(f"  within-colony variance  : model {var_within:8.3f} | "
          f"closed form {check['var_within']:8.3f} mg^2")
    print(f"  exposure effect         : model {effect:8.3f} | "
          f"closed form {check['effect']:8.3f} mg")
    print(f"  standard error          : model {se:8.3f} | "
          f"closed form {check['se']:8.3f} mg")
    agree = (
        abs(var_between - check["var_between"]) < 0.01
        and abs(var_within - check["var_within"]) < 0.01
        and abs(se - check["se"]) < 0.01
    )
    print(f"  agreement               : "
          f"{'OK - optimiser converged' if agree else 'MISMATCH'}")
    if not agree:
        raise RuntimeError(
            "The mixed-model optimiser disagrees with the exact closed-form "
            "REML solution for this balanced design. Do not report these "
            "numbers."
        )
    print()

    verdict = "is" if pval < ALPHA else "is not"
    print(f"At alpha = {ALPHA}, the exposure effect {verdict} statistically "
          f"significant in the primary model.")
    print()

    return {
        "effect": effect, "se": se, "ci_low": ci_low, "ci_high": ci_high,
        "z": zval, "p": pval, "p_small": float(p_small), "df_small": df_small,
        "ci_low_t": float(ci_low_t), "ci_high_t": float(ci_high_t),
        "var_between": var_between, "var_within": var_within, "icc": icc,
        "control_mean": control_mean,
    }


# ---------------------------------------------------------------------------
# Secondary sensitivity analysis
# ---------------------------------------------------------------------------

def secondary_row_level_ttest(df):
    """Naive two-sample t-test on all 160 rows. Sensitivity check only."""
    print("=" * 78)
    print("SECONDARY SENSITIVITY ANALYSIS - ROW-LEVEL TWO-SAMPLE t-TEST")
    print("IT IGNORES COLONY STRUCTURE AND IS NOT THE BASIS FOR ANY "
          "CONCLUSION.")
    print("=" * 78)
    print("This test treats all 160 foragers as independent observations of")
    print("the treatment. They are not: the fungicide was applied 16 times,")
    print("once per colony. The test therefore overstates the number of")
    print("independent observations and understates the standard error.")
    print()

    control = df.loc[df["exposure_group"] == "control", "fragment_mass_mg"]
    exposed = df.loc[df["exposure_group"] == "exposed", "fragment_mass_mg"]

    tstat, pval = st.ttest_ind(exposed, control, equal_var=False)

    n1, n2 = len(exposed), len(control)
    v1, v2 = exposed.var(ddof=1), control.var(ddof=1)
    diff = exposed.mean() - control.mean()
    se = np.sqrt(v1 / n1 + v2 / n2)
    dof = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    tcrit = st.t.ppf(1 - ALPHA / 2, dof)
    ci_low, ci_high = diff - tcrit * se, diff + tcrit * se

    print("Test  : Welch's independent two-sample t-test, two-sided")
    print(f"n (control foragers)             : {n2}")
    print(f"n (exposed foragers)             : {n1}")
    print(f"Mean, control foragers           : {control.mean():8.3f} mg")
    print(f"Mean, exposed foragers           : {exposed.mean():8.3f} mg")
    print(f"Difference (exposed - control)   : {diff:8.3f} mg")
    print(f"Standard error                   : {se:8.3f} mg")
    print(f"95% confidence interval          : "
          f"[{ci_low:.3f}, {ci_high:.3f}] mg")
    print(f"t statistic                      : {tstat:8.3f}")
    print(f"Welch degrees of freedom         : {dof:8.2f}")
    print(f"p-value                          : {pval:.6g}")
    print()
    print("Reminder: secondary only. The mixed model above is the inferential")
    print("result of this project.")
    print()

    return {
        "diff": float(diff), "se": float(se), "ci_low": float(ci_low),
        "ci_high": float(ci_high), "t": float(tstat), "dof": float(dof),
        "p": float(pval), "mean_control": float(control.mean()),
        "mean_exposed": float(exposed.mean()),
    }


# ---------------------------------------------------------------------------

def main():
    df = load_data(CSV_PATH)
    describe_design(df)
    check = balanced_reml_check(df)
    primary = primary_mixed_model(df, check)
    secondary = secondary_row_level_ttest(df)

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print("PRIMARY - mixed model with colony random effect. "
          "This is the result.")
    print(f"  exposure effect {primary['effect']:.3f} mg, "
          f"SE {primary['se']:.3f} mg, "
          f"95% CI [{primary['ci_low']:.3f}, {primary['ci_high']:.3f}] mg, "
          f"p = {primary['p']:.5f} (Wald z)")
    print(f"  small-sample check: 95% CI "
          f"[{primary['ci_low_t']:.3f}, {primary['ci_high_t']:.3f}] mg, "
          f"p = {primary['p_small']:.5f} (t, {primary['df_small']} df)")
    print(f"  between-colony variance {primary['var_between']:.3f} mg^2, "
          f"within-colony variance {primary['var_within']:.3f} mg^2, "
          f"ICC {primary['icc']:.3f}")
    print()
    print("SECONDARY - row-level t-test ignoring colony structure. "
          "NOT a conclusion.")
    print(f"  difference {secondary['diff']:.3f} mg, "
          f"SE {secondary['se']:.3f} mg, "
          f"95% CI [{secondary['ci_low']:.3f}, {secondary['ci_high']:.3f}] mg,"
          f" p = {secondary['p']:.6g}")
    print(f"  the primary standard error is "
          f"{primary['se'] / secondary['se']:.2f} times larger than this one,"
          f" because this test pretends 160 foragers are 160 independent "
          f"units.")
    print()
    print(f"Fitted with statsmodels {sm.__version__}, pandas {pd.__version__}, "
          f"scipy {scipy.__version__}, numpy {np.__version__}.")


if __name__ == "__main__":
    main()
