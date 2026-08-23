"""Green turtle hatchling carapace length by incubation substrate.

Question
--------
Does straight carapace length at emergence differ between hatchlings incubated
in native beach sand and hatchlings incubated in coarser imported sand?

Design
------
Substrate was assigned to whole clutches (12 clutches per substrate), and ten
hatchlings were measured inside each clutch. The clutch, not the hatchling, is
the independent experimental unit: the ten rows inside a clutch are siblings
from one mother's single clutch, sharing an egg chamber and a thermal history.

What this script does
---------------------
1. Loads and structurally checks the frozen CSV.
2. Describes the outcome at hatchling level and at clutch level.
3. PRIMARY inference: a linear mixed-effects model (statsmodels) with a random
   intercept for clutch, so the dependence between siblings is modelled rather
   than ignored.
4. SUPPORTING check: a cluster bootstrap that resamples whole clutches with
   replacement, recomputes the substrate difference in each resample, and forms
   a percentile interval and p-value from that distribution.
5. ILLUSTRATIVE CONTRAST ONLY: a plain independent two-sample t-test over the
   240 raw hatchling rows. This treats siblings as independent replicates and
   is NOT a valid basis for inference here. It is computed purely to show how
   much narrower and more confident the naive comparison looks.

Run with: python3 analysis.py
"""

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf

DATA_FILE = "hatchling_carapace.csv"
OUTCOME = "carapace_length_mm"
CLUSTER = "clutch_ref"
GROUP = "substrate"
REFERENCE_LEVEL = "imported"   # so the reported effect is native minus imported
BOOTSTRAP_DRAWS = 20000
BOOTSTRAP_SEED = 20260822
ALPHA = 0.05


def load_data(path=DATA_FILE):
    """Read the frozen CSV and check the structure the protocol assumes."""
    df = pd.read_csv(path)

    expected_columns = [CLUSTER, GROUP, "hatchling_number", OUTCOME]
    assert list(df.columns) == expected_columns, f"unexpected columns: {list(df.columns)}"
    assert not df.isna().any().any(), "missing values present"

    # Substrate is a clutch-level property: exactly one substrate per clutch.
    per_clutch = df.groupby(CLUSTER).agg(
        n_rows=(OUTCOME, "size"),
        n_substrates=(GROUP, "nunique"),
    )
    assert (per_clutch["n_substrates"] == 1).all(), "a clutch carries more than one substrate"
    assert (per_clutch["n_rows"] == 10).all(), "clutches do not all hold ten hatchlings"

    return df


def describe(df):
    """Hatchling-level and clutch-level summaries of the outcome."""
    clutch_means = (
        df.groupby([CLUSTER, GROUP], as_index=False)[OUTCOME]
        .mean()
        .rename(columns={OUTCOME: "clutch_mean_mm"})
    )

    hatchling_summary = df.groupby(GROUP)[OUTCOME].agg(
        n_hatchlings="size", mean="mean", sd=lambda s: s.std(ddof=1)
    )
    clutch_summary = clutch_means.groupby(GROUP)["clutch_mean_mm"].agg(
        n_clutches="size", mean="mean", sd=lambda s: s.std(ddof=1)
    )
    return clutch_means, hatchling_summary, clutch_summary


def primary_mixed_model(df):
    """PRIMARY: random-intercept model, clutch as the grouping factor.

    carapace_length_mm ~ substrate + (1 | clutch_ref)

    The random intercept gives every clutch its own offset, which is how the
    model respects the fact that siblings resemble one another. Fitted by REML
    with statsmodels; scipy has no mixed-model facility.
    """
    model_df = df.copy()
    model_df[GROUP] = pd.Categorical(
        model_df[GROUP], categories=[REFERENCE_LEVEL, "native"]
    )

    fit = smf.mixedlm(
        f"{OUTCOME} ~ C({GROUP}, Treatment(reference='{REFERENCE_LEVEL}'))",
        data=model_df,
        groups=model_df[CLUSTER],
    ).fit(reml=True)

    term = [t for t in fit.params.index if t.startswith(f"C({GROUP}")][0]
    estimate = float(fit.params[term])
    stderr = float(fit.bse[term])
    pvalue = float(fit.pvalues[term])
    lo, hi = (float(v) for v in fit.conf_int(alpha=ALPHA).loc[term])

    between_var = float(fit.cov_re.iloc[0, 0])
    within_var = float(fit.scale)
    icc = between_var / (between_var + within_var)

    return {
        "fit": fit,
        "term": term,
        "estimate": estimate,
        "stderr": stderr,
        "pvalue": pvalue,
        "ci": (lo, hi),
        "between_clutch_sd": np.sqrt(between_var),
        "within_clutch_sd": np.sqrt(within_var),
        "icc": icc,
    }


def cluster_bootstrap(df, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    """SUPPORTING: resample whole clutches with replacement.

    The resampling unit is the clutch, never the individual hatchling. Within
    each substrate arm, 12 clutch labels are drawn with replacement from that
    arm's 12 clutches; every hatchling row of a drawn clutch travels with it, so
    sibling dependence is carried into each resample. The statistic recomputed
    in each resample is the difference in mean carapace length, native minus
    imported, over the resampled hatchling rows.
    """
    rows_by_clutch = {ref: g[OUTCOME].to_numpy() for ref, g in df.groupby(CLUSTER)}
    arms = {
        arm: sorted(g[CLUSTER].unique())
        for arm, g in df.groupby(GROUP)
    }

    def arm_mean(clutch_refs):
        return np.concatenate([rows_by_clutch[r] for r in clutch_refs]).mean()

    observed = arm_mean(arms["native"]) - arm_mean(arms[REFERENCE_LEVEL])

    rng = np.random.default_rng(seed)
    diffs = np.empty(draws)
    for i in range(draws):
        native = rng.choice(arms["native"], size=len(arms["native"]), replace=True)
        imported = rng.choice(arms[REFERENCE_LEVEL], size=len(arms[REFERENCE_LEVEL]), replace=True)
        diffs[i] = arm_mean(native) - arm_mean(imported)

    lo, hi = np.percentile(diffs, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])

    # Two-sided p-value read off the resample distribution: twice the smaller
    # tail mass on the far side of no difference, floored at 1/(draws + 1)
    # because the bootstrap cannot resolve anything finer than its own grid.
    tail = min((diffs <= 0).mean(), (diffs >= 0).mean())
    pvalue = max(2 * tail, 1.0 / (draws + 1))

    return {
        "observed": observed,
        "ci": (float(lo), float(hi)),
        "pvalue": float(pvalue),
        "se": float(diffs.std(ddof=1)),
        "draws": draws,
        "floored": 2 * tail < 1.0 / (draws + 1),
    }


def naive_hatchling_ttest(df):
    """ILLUSTRATIVE CONTRAST ONLY -- NOT A VALID INFERENCE FOR THIS DESIGN.

    A plain independent two-sample t-test over the 240 raw hatchling rows. It
    counts each of the ten siblings in a clutch as a separate independent
    replicate, which they are not, so it borrows precision the design never
    delivered. Reported only to show how much narrower and more confident that
    mistake makes the comparison look.
    """
    native = df.loc[df[GROUP] == "native", OUTCOME].to_numpy()
    imported = df.loc[df[GROUP] == REFERENCE_LEVEL, OUTCOME].to_numpy()

    result = st.ttest_ind(native, imported, equal_var=True)
    diff = native.mean() - imported.mean()

    n1, n2 = len(native), len(imported)
    dof = n1 + n2 - 2
    pooled_var = (
        (n1 - 1) * native.var(ddof=1) + (n2 - 1) * imported.var(ddof=1)
    ) / dof
    stderr = np.sqrt(pooled_var * (1 / n1 + 1 / n2))
    margin = st.t.ppf(1 - ALPHA / 2, dof) * stderr

    return {
        "diff": float(diff),
        "stderr": float(stderr),
        "ci": (float(diff - margin), float(diff + margin)),
        "pvalue": float(result.pvalue),
        "tstat": float(result.statistic),
        "dof": dof,
    }


def main():
    df = load_data()
    clutch_means, hatchling_summary, clutch_summary = describe(df)

    n_hatchlings = len(df)
    n_clutches = df[CLUSTER].nunique()

    print("=" * 74)
    print("Carapace length by incubation substrate")
    print("=" * 74)
    print(f"Hatchlings (rows): {n_hatchlings}")
    print(f"Clutches (independent units): {n_clutches}")
    print(f"Hatchlings per clutch: {df.groupby(CLUSTER).size().unique().tolist()}")
    print()

    print("-- Hatchling-level summary (mm) " + "-" * 41)
    print(hatchling_summary.to_string(float_format=lambda v: f"{v:.3f}"))
    print()
    print("-- Clutch-mean summary (mm) " + "-" * 45)
    print(clutch_summary.to_string(float_format=lambda v: f"{v:.3f}"))
    print()
    print("-- Clutch means (mm) " + "-" * 52)
    print(clutch_means.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print()

    primary = primary_mixed_model(df)
    print("=" * 74)
    print("PRIMARY: linear mixed-effects model, random intercept for clutch")
    print("=" * 74)
    print(primary["fit"].summary())
    print()
    lo, hi = primary["ci"]
    print(f"Effect (native - imported): {primary['estimate']:+.4f} mm")
    print(f"  standard error:           {primary['stderr']:.4f} mm")
    print(f"  95% CI:                   [{lo:+.4f}, {hi:+.4f}] mm")
    print(f"  p-value:                  {primary['pvalue']:.6f}")
    print(f"  between-clutch SD:        {primary['between_clutch_sd']:.4f} mm")
    print(f"  within-clutch SD:         {primary['within_clutch_sd']:.4f} mm")
    print(f"  intraclass correlation:   {primary['icc']:.4f}")
    print()

    boot = cluster_bootstrap(df)
    blo, bhi = boot["ci"]
    print("=" * 74)
    print("SUPPORTING: cluster bootstrap over whole clutches")
    print("=" * 74)
    print(f"Resampling unit: whole clutch (all 10 sibling rows move together)")
    print(f"Resamples: {boot['draws']} (seed {BOOTSTRAP_SEED})")
    print(f"Observed difference (native - imported): {boot['observed']:+.4f} mm")
    print(f"  bootstrap SE:              {boot['se']:.4f} mm")
    print(f"  95% percentile CI:         [{blo:+.4f}, {bhi:+.4f}] mm")
    print(f"  two-sided p-value:         {boot['pvalue']:.6f}"
          + ("  (floor 1/(B+1); no resample crossed zero)" if boot["floored"] else ""))
    print()

    naive = naive_hatchling_ttest(df)
    nlo, nhi = naive["ci"]
    print("=" * 74)
    print("ILLUSTRATIVE CONTRAST ONLY -- NOT VALID INFERENCE FOR THIS DESIGN")
    print("=" * 74)
    print("Independent two-sample t-test over the 240 raw hatchling rows,")
    print("which wrongly counts each sibling as an independent replicate.")
    print(f"Difference (native - imported): {naive['diff']:+.4f} mm")
    print(f"  standard error:               {naive['stderr']:.4f} mm")
    print(f"  95% CI:                       [{nlo:+.4f}, {nhi:+.4f}] mm")
    print(f"  t({naive['dof']}) = {naive['tstat']:.4f}")
    print(f"  p-value:                      {naive['pvalue']:.6e}")
    print()
    print(f"Naive CI width {nhi - nlo:.4f} mm vs primary CI width {hi - lo:.4f} mm "
          f"(ratio {(hi - lo) / (nhi - nlo):.2f}x wider for the valid procedure).")
    print()
    print("Conclusion rests on the clutch-aware procedure alone.")


if __name__ == "__main__":
    main()
