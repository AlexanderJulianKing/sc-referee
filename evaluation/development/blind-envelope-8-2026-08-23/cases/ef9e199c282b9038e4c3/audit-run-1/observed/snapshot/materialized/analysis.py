"""Analysis of zebra finch song bout duration under chronic traffic-like noise.

Design
------
Fourteen adult male zebra finches were housed individually for six weeks, seven in a
room with playback of low-frequency traffic-like noise and seven in a quiet room.
Twelve complete song bouts were then recorded from every bird, giving 168 rows.

The bird is the independent experimental unit. Housing condition was assigned to the
bird, not to the bout, so the twelve rows of a bird are repeated measures of one
individual and are not independent of one another.

Primary inference
-----------------
A linear mixed-effects model of bout duration on housing condition with a random
intercept for each bird. The random intercept absorbs the stable between-bird
differences in song length, so the condition effect is tested against between-bird
variation rather than against bout-to-bout variation.

Secondary
---------
Two clearly labelled sensitivity checks that are NOT the inferential result:
  (S1) a plain two-sample t-test over all 168 rows, which ignores the nesting and
       treats each bout as an independent observation;
  (S2) a two-sample t-test over the 14 per-bird mean durations, which respects the
       independent unit but discards the within-bird information.

Run with:  python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

DATA_FILE = "zebra_finch_song_bouts.csv"
OUTCOME = "bout_duration_s"
GROUP_COL = "bird_id"
CONDITION_COL = "noise_condition"
REFERENCE_LEVEL = "quiet"   # effect is reported as noise minus quiet
ALPHA = 0.05


def load_data():
    """Read the frozen CSV from the project root and check the stated structure."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    df = pd.read_csv(path)

    expected_columns = [
        "bird_id",
        "noise_condition",
        "bout_number",
        "bout_duration_s",
        "motif_count",
        "peak_frequency_khz",
        "recording_time",
        "age_days",
    ]
    assert list(df.columns) == expected_columns, f"unexpected columns: {list(df.columns)}"
    assert not df.isna().any().any(), "data contains missing cells"

    # Condition must be a property of the bird, constant across its bouts.
    per_bird_conditions = df.groupby(GROUP_COL)[CONDITION_COL].nunique()
    assert (per_bird_conditions == 1).all(), "a bird appears in more than one condition"

    return df


def describe(df):
    """Counts that the report must state, plus simple descriptive statistics."""
    n_birds = df[GROUP_COL].nunique()
    n_bouts = len(df)
    bouts_per_bird = df.groupby(GROUP_COL).size()

    bird_level = (
        df.groupby([GROUP_COL, CONDITION_COL], as_index=False)[OUTCOME]
        .mean()
        .rename(columns={OUTCOME: "mean_bout_duration_s"})
    )

    print("=" * 72)
    print("STRUCTURE AND DESCRIPTIVE STATISTICS")
    print("=" * 72)
    print(f"Birds (independent units): {n_birds}")
    print(f"Song bouts (rows)        : {n_bouts}")
    print(f"Bouts per bird           : min {bouts_per_bird.min()}, max {bouts_per_bird.max()}")
    print()
    print("Birds per condition:")
    print(bird_level.groupby(CONDITION_COL).size().to_string())
    print()
    print("Bout-level duration by condition (all 168 rows):")
    bout_summary = df.groupby(CONDITION_COL)[OUTCOME].agg(["count", "mean", "std", "min", "max"])
    print(bout_summary.round(4).to_string())
    print()
    print("Bird-mean duration by condition (14 birds):")
    bird_summary = bird_level.groupby(CONDITION_COL)["mean_bout_duration_s"].agg(
        ["count", "mean", "std", "min", "max"]
    )
    print(bird_summary.round(4).to_string())
    print()
    print("Per-bird mean bout duration:")
    print(bird_level.round(4).to_string(index=False))
    print()

    return n_birds, n_bouts, bird_level


def primary_mixed_model(df):
    """Random-intercept linear mixed-effects model: the study's primary inference."""
    print("=" * 72)
    print("PRIMARY ANALYSIS: linear mixed-effects model, random intercept per bird")
    print("=" * 72)
    print(f"Model    : {OUTCOME} ~ {CONDITION_COL} + (1 | {GROUP_COL})")
    print(f"Reference: {CONDITION_COL} = '{REFERENCE_LEVEL}'  (effect = noise minus quiet)")
    print("Estimated by restricted maximum likelihood (REML).")
    print()

    formula = f"{OUTCOME} ~ C({CONDITION_COL}, Treatment(reference='{REFERENCE_LEVEL}'))"
    model = smf.mixedlm(formula, data=df, groups=df[GROUP_COL], re_formula="1")
    fit = model.fit(reml=True, method="lbfgs")

    print(fit.summary())
    print()

    # Locate the condition coefficient by name.
    term = [n for n in fit.params.index if CONDITION_COL in n]
    assert len(term) == 1, f"expected one condition term, found {term}"
    term = term[0]

    effect = float(fit.params[term])
    se = float(fit.bse[term])
    z = float(fit.tvalues[term])
    p = float(fit.pvalues[term])
    ci_low, ci_high = (float(v) for v in fit.conf_int().loc[term])

    # Variance components and the intraclass correlation.
    var_bird = float(fit.cov_re.iloc[0, 0])
    var_resid = float(fit.scale)
    icc = var_bird / (var_bird + var_resid)

    print("-" * 72)
    print("PRIMARY RESULT")
    print("-" * 72)
    print(f"Condition effect (noise - quiet): {effect:+.4f} s")
    print(f"Standard error                  : {se:.4f} s")
    print(f"95% Wald confidence interval    : [{ci_low:+.4f}, {ci_high:+.4f}] s")
    print(f"Test statistic (Wald z)         : {z:.4f}")
    print(f"p-value                         : {p:.6f}")
    print()
    print(f"Between-bird variance (random intercept): {var_bird:.6f} s^2 "
          f"(SD {np.sqrt(var_bird):.4f} s)")
    print(f"Within-bird residual variance           : {var_resid:.6f} s^2 "
          f"(SD {np.sqrt(var_resid):.4f} s)")
    print(f"Intraclass correlation (ICC)            : {icc:.4f}")
    print()
    print("The Wald z-test above is the p-value the model reports. It is an asymptotic")
    print("test; with only 14 birds a small-sample reference distribution is more")
    print("conservative, so check S2 below is reported alongside it.")
    print()

    return {
        "effect": effect,
        "se": se,
        "z": z,
        "p": p,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "var_bird": var_bird,
        "var_resid": var_resid,
        "icc": icc,
    }


def secondary_checks(df, bird_level):
    """Sensitivity checks. NOT the inferential result of the study."""
    print("=" * 72)
    print("SECONDARY SENSITIVITY CHECKS (not the inferential result)")
    print("=" * 72)

    # S1: naive two-sample t-test over all 168 rows.
    noise_rows = df.loc[df[CONDITION_COL] == "noise", OUTCOME].to_numpy()
    quiet_rows = df.loc[df[CONDITION_COL] == "quiet", OUTCOME].to_numpy()
    t1, p1 = stats.ttest_ind(noise_rows, quiet_rows, equal_var=True)
    diff1 = noise_rows.mean() - quiet_rows.mean()
    df1 = len(noise_rows) + len(quiet_rows) - 2

    print("S1. Plain two-sample t-test over all rows (pseudoreplicated)")
    print(f"    n = {len(noise_rows)} noise rows vs {len(quiet_rows)} quiet rows, df = {df1}")
    print(f"    mean difference (noise - quiet): {diff1:+.4f} s")
    print(f"    t = {t1:.4f}, p = {p1:.6g}")
    print("    This check treats each of the 168 bouts as an independent observation.")
    print("    It is not valid for the study question: condition was assigned to birds,")
    print("    so there are 14 independent units, not 168.")
    print()

    # S2: two-sample t-test over the 14 per-bird means.
    noise_birds = bird_level.loc[
        bird_level[CONDITION_COL] == "noise", "mean_bout_duration_s"
    ].to_numpy()
    quiet_birds = bird_level.loc[
        bird_level[CONDITION_COL] == "quiet", "mean_bout_duration_s"
    ].to_numpy()
    t2, p2 = stats.ttest_ind(noise_birds, quiet_birds, equal_var=True)
    diff2 = noise_birds.mean() - quiet_birds.mean()
    df2 = len(noise_birds) + len(quiet_birds) - 2
    sp = np.sqrt(
        ((len(noise_birds) - 1) * noise_birds.var(ddof=1)
         + (len(quiet_birds) - 1) * quiet_birds.var(ddof=1)) / df2
    )
    se2 = sp * np.sqrt(1 / len(noise_birds) + 1 / len(quiet_birds))
    tcrit = stats.t.ppf(1 - ALPHA / 2, df2)

    print("S2. Two-sample t-test over the 14 per-bird mean durations")
    print(f"    n = {len(noise_birds)} noise birds vs {len(quiet_birds)} quiet birds, df = {df2}")
    print(f"    mean difference (noise - quiet): {diff2:+.4f} s")
    print(f"    standard error: {se2:.4f} s")
    print(f"    95% CI: [{diff2 - tcrit * se2:+.4f}, {diff2 + tcrit * se2:+.4f}] s")
    print(f"    t = {t2:.4f}, p = {p2:.6g}")
    print("    This check uses the correct independent unit but collapses each bird to")
    print("    one number, discarding the within-bird information the primary model uses.")
    print()

    return {
        "s1_diff": float(diff1), "s1_t": float(t1), "s1_p": float(p1), "s1_df": int(df1),
        "s2_diff": float(diff2), "s2_t": float(t2), "s2_p": float(p2), "s2_df": int(df2),
        "s2_se": float(se2),
        "s2_ci_low": float(diff2 - tcrit * se2),
        "s2_ci_high": float(diff2 + tcrit * se2),
    }


def main():
    df = load_data()
    n_birds, n_bouts, bird_level = describe(df)
    primary = primary_mixed_model(df)
    secondary = secondary_checks(df, bird_level)

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Birds: {n_birds}   Bouts: {n_bouts}")
    print(
        "PRIMARY (mixed model, random intercept per bird): "
        f"effect {primary['effect']:+.3f} s, SE {primary['se']:.3f}, "
        f"95% CI [{primary['ci_low']:+.3f}, {primary['ci_high']:+.3f}], "
        f"z = {primary['z']:.2f}, p = {primary['p']:.4f}"
    )
    print(
        f"SECONDARY S1 (all rows, pseudoreplicated): p = {secondary['s1_p']:.3g} "
        "- sensitivity check only"
    )
    print(
        f"SECONDARY S2 (per-bird means): p = {secondary['s2_p']:.3g} "
        "- sensitivity check only"
    )


if __name__ == "__main__":
    main()
