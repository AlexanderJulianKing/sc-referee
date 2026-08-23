"""Analysis of the cuttlefish enrichment experiment.

Question
--------
Does structural enrichment of the holding tank change hunting motivation in
juvenile common cuttlefish, measured as latency to first tentacle strike?

Design
------
Twenty animals, ten housed in enriched holdings and ten in bare holdings. Each
animal was given six prey-presentation trials on separate days, giving 120
trial-level rows. The animal is the unit that was assigned to a housing
condition; the six rows within an animal are repeated behavioural trials on the
same individual and are therefore not independent of one another.

Analyses
--------
PRIMARY (inferential): a linear mixed-effects model fitted to the 120
trial-level rows, with housing as the fixed effect of interest and a random
intercept for animal_ref. The random intercept is what accounts for the
repeated-measures structure. The housing estimate, its standard error and its
p-value are taken from this model, and the conclusion of the study is stated
from it.

SECONDARY (sensitivity check only): a plain independent two-sample comparison
of means over the raw trial-level rows. This treats the 120 rows as 120
independent observations, which they are not. It is reported only to show that
the direction of the effect is not an artefact of the modelling choice. It is
not the basis for the conclusion.

Run with: python3 analysis.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

DATA_FILE = Path(__file__).resolve().parent / "cuttlefish_strike_latency.csv"

OUTCOME = "strike_latency_s"
GROUP_COL = "housing"
UNIT_COL = "animal_ref"
REFERENCE_LEVEL = "bare"
COMPARISON_LEVEL = "enriched"


def load_data(path=DATA_FILE):
    """Read the frozen CSV and check the structure the analysis assumes."""
    df = pd.read_csv(path)

    expected_columns = [UNIT_COL, GROUP_COL, "trial_number", OUTCOME]
    if list(df.columns) != expected_columns:
        raise ValueError(f"unexpected columns: {list(df.columns)}")
    if df.isna().any().any():
        raise ValueError("missing values present; the analysis assumes none")

    observed_levels = set(df[GROUP_COL].unique())
    if observed_levels != {REFERENCE_LEVEL, COMPARISON_LEVEL}:
        raise ValueError(f"unexpected housing levels: {sorted(observed_levels)}")

    # Housing must be constant within an animal, otherwise it is not a
    # between-animal factor and the model below would be misspecified.
    per_animal_levels = df.groupby(UNIT_COL)[GROUP_COL].nunique()
    if (per_animal_levels != 1).any():
        raise ValueError("housing varies within at least one animal")

    return df


def describe(df):
    """Descriptive summary of the delivered file. No inference here."""
    n_animals = df[UNIT_COL].nunique()
    n_trials = len(df)

    print("=" * 72)
    print("DATA")
    print("=" * 72)
    print(f"File                : {DATA_FILE.name}")
    print(f"Animals             : {n_animals}")
    print(f"Trial-level rows    : {n_trials}")
    print(f"Trials per animal   : {df.groupby(UNIT_COL).size().unique().tolist()}")
    print()

    by_group = (
        df.groupby(GROUP_COL)
        .agg(
            animals=(UNIT_COL, "nunique"),
            rows=(OUTCOME, "size"),
            mean_s=(OUTCOME, "mean"),
            sd_rows_s=(OUTCOME, "std"),
            min_s=(OUTCOME, "min"),
            max_s=(OUTCOME, "max"),
        )
        .round(3)
    )
    print("Trial-level summary by housing group:")
    print(by_group.to_string())
    print()

    animal_means = df.groupby([UNIT_COL, GROUP_COL], as_index=False)[OUTCOME].mean()
    by_group_animal = (
        animal_means.groupby(GROUP_COL)[OUTCOME]
        .agg(animals="size", mean_of_animal_means="mean", sd_of_animal_means="std")
        .round(3)
    )
    print("Animal-mean summary by housing group:")
    print(by_group_animal.to_string())
    print()

    return {
        "n_animals": n_animals,
        "n_trials": n_trials,
        "by_group": by_group,
        "by_group_animal": by_group_animal,
        "animal_means": animal_means,
    }


def primary_mixed_model(df):
    """PRIMARY inference: random-intercept model on the trial-level rows.

    strike_latency_s ~ housing + (1 | animal_ref)

    Housing is coded with `bare` as the reference level, so the housing
    coefficient is the enriched-minus-bare difference in seconds.
    """
    model = smf.mixedlm(
        f"{OUTCOME} ~ C({GROUP_COL}, Treatment(reference='{REFERENCE_LEVEL}'))",
        data=df,
        groups=df[UNIT_COL],
    )
    fit = model.fit(reml=True)

    term = [t for t in fit.params.index if t.startswith(f"C({GROUP_COL}")][0]

    estimate = float(fit.params[term])
    std_err = float(fit.bse[term])
    p_value = float(fit.pvalues[term])
    ci_low, ci_high = (float(x) for x in fit.conf_int().loc[term])

    # Variance components: between-animal vs within-animal (residual).
    between_var = float(np.asarray(fit.cov_re)[0, 0])
    within_var = float(fit.scale)
    icc = between_var / (between_var + within_var)

    print("=" * 72)
    print("PRIMARY ANALYSIS (inferential): linear mixed-effects model")
    print("=" * 72)
    print(f"Formula        : {OUTCOME} ~ {GROUP_COL} + (1 | {UNIT_COL})")
    print(f"Estimation     : REML; Wald z-test on the fixed effect")
    print(f"Groups (animals): {int(fit.model.n_groups)}   Rows: {int(fit.nobs)}")
    print()
    print(fit.summary())
    print()
    print(f"Housing effect ({COMPARISON_LEVEL} minus {REFERENCE_LEVEL}):")
    print(f"  estimate        = {estimate:+.4f} s")
    print(f"  standard error  = {std_err:.4f} s")
    print(f"  z               = {estimate / std_err:+.4f}")
    print(f"  p-value         = {p_value:.6g}")
    print(f"  95% CI          = [{ci_low:+.4f}, {ci_high:+.4f}] s")
    print()
    print(f"  between-animal SD (random intercept) = {between_var ** 0.5:.4f} s")
    print(f"  within-animal SD (residual)          = {within_var ** 0.5:.4f} s")
    print(f"  intraclass correlation               = {icc:.4f}")
    print()

    return {
        "estimate": estimate,
        "std_err": std_err,
        "z": estimate / std_err,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "between_sd": between_var ** 0.5,
        "within_sd": within_var ** 0.5,
        "icc": icc,
        "n_groups": int(fit.model.n_groups),
        "n_obs": int(fit.nobs),
    }


def secondary_row_level_ttest(df):
    """SECONDARY sensitivity check ONLY. Not the inferential result.

    A plain independent two-sample comparison of means over the 120 raw
    trial-level rows. This ignores the repeated-measures structure: it treats
    the six trials on one animal as six independent observations, so its
    standard error and p-value are not trustworthy for this design. It is run
    only to show the direction of the effect does not depend on the model.
    """
    enriched = df.loc[df[GROUP_COL] == COMPARISON_LEVEL, OUTCOME].to_numpy()
    bare = df.loc[df[GROUP_COL] == REFERENCE_LEVEL, OUTCOME].to_numpy()

    # Welch's version (does not assume equal group variances).
    t_welch, p_welch = stats.ttest_ind(enriched, bare, equal_var=False)
    # Student's version (assumes equal group variances), for completeness.
    t_student, p_student = stats.ttest_ind(enriched, bare, equal_var=True)

    diff = float(enriched.mean() - bare.mean())
    se_welch = float(
        np.sqrt(enriched.var(ddof=1) / enriched.size + bare.var(ddof=1) / bare.size)
    )
    df_welch = (
        (enriched.var(ddof=1) / enriched.size + bare.var(ddof=1) / bare.size) ** 2
        / (
            (enriched.var(ddof=1) / enriched.size) ** 2 / (enriched.size - 1)
            + (bare.var(ddof=1) / bare.size) ** 2 / (bare.size - 1)
        )
    )

    print("=" * 72)
    print("SECONDARY CHECK (NOT the inferential result): row-level t-test")
    print("=" * 72)
    print("This comparison ignores the repeated-measures structure. It treats the")
    print("120 trial rows as 120 independent observations, which they are not.")
    print("Direction check only; the study conclusion is NOT based on it.")
    print()
    print(f"  n rows          : {enriched.size} {COMPARISON_LEVEL}, {bare.size} {REFERENCE_LEVEL}")
    print(f"  means           : {enriched.mean():.4f} s vs {bare.mean():.4f} s")
    print(f"  difference      = {diff:+.4f} s ({COMPARISON_LEVEL} minus {REFERENCE_LEVEL})")
    print(f"  Welch  SE       = {se_welch:.4f} s, t = {t_welch:+.4f}, df = {df_welch:.2f}, p = {p_welch:.6g}")
    print(f"  Student t       = {t_student:+.4f}, df = {enriched.size + bare.size - 2}, p = {p_student:.6g}")
    print()

    return {
        "n_enriched": int(enriched.size),
        "n_bare": int(bare.size),
        "mean_enriched": float(enriched.mean()),
        "mean_bare": float(bare.mean()),
        "diff": diff,
        "se_welch": se_welch,
        "t_welch": float(t_welch),
        "df_welch": float(df_welch),
        "p_welch": float(p_welch),
        "t_student": float(t_student),
        "p_student": float(p_student),
    }


def main():
    df = load_data()
    desc = describe(df)
    primary = primary_mixed_model(df)
    secondary = secondary_row_level_ttest(df)

    print("=" * 72)
    print("CONCLUSION (from the PRIMARY mixed-effects model only)")
    print("=" * 72)
    direction = "shorter" if primary["estimate"] < 0 else "longer"
    print(
        f"Animals in enriched housing struck {abs(primary['estimate']):.2f} s "
        f"{direction} than bare-housed animals "
        f"(SE {primary['std_err']:.2f} s, p = {primary['p_value']:.4g}), "
        f"from {primary['n_groups']} animals and {primary['n_obs']} trials."
    )
    print()
    print("statsmodels version:", sm.__version__)

    return desc, primary, secondary


if __name__ == "__main__":
    main()
