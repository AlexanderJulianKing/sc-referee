"""Analysis of the Scots pine nursery inoculant trial.

Primary inference: difference in mean seedling height (inoculated minus
uninoculated) with uncertainty from a hand-written cluster bootstrap that
resamples whole nursery BENCHES, not individual seedlings.

The bench is the unit that was assigned to a treatment (one bench = one
irrigation valve = one batch of growing medium), and the fifteen seedlings on a
bench are not independent of one another. So the resampling has to draw benches
as intact blocks; resampling seedlings would pretend there are 90 independent
observations per arm when there are only 6.

A plain seedling-level two-sample test is also computed, purely as an
illustrative contrast. It is NOT a valid inference for this design.

Run:  /usr/local/bin/python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

SEED = 20260822
N_RESAMPLES = 10000
CI_LEVEL = 0.95

DATA_NAME = "seedlings.csv"
OUTCOME = "heightCm"
GROUP = "inoculantTreatment"
CLUSTER = "benchNo"
TREATED = "inoculated"
CONTROL = "uninoculated"


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_NAME)
    df = pd.read_csv(path)

    # Structural checks: the design claims must hold in the file itself.
    assert set(df[GROUP].unique()) == {TREATED, CONTROL}, "unexpected treatment labels"
    assert df[OUTCOME].notna().all(), "missing heights"
    per_bench = df.groupby(CLUSTER)[GROUP].nunique()
    assert (per_bench == 1).all(), "a bench carries more than one treatment label"
    return df


def bench_table(df):
    """One row per bench: its treatment, its seedling count, its mean height."""
    out = (
        df.groupby([CLUSTER, GROUP])[OUTCOME]
        .agg(nSeedlings="size", meanHeightCm="mean", sdHeightCm="std")
        .reset_index()
        .sort_values(CLUSTER)
    )
    return out


def observed_difference(df):
    """Difference in mean height, treated minus control, over all seedling rows."""
    m_t = df.loc[df[GROUP] == TREATED, OUTCOME].mean()
    m_c = df.loc[df[GROUP] == CONTROL, OUTCOME].mean()
    return m_t - m_c, m_t, m_c


def cluster_bootstrap(df, n_resamples=N_RESAMPLES, seed=SEED):
    """Hand-written cluster (bench-level) bootstrap, coded from first principles.

    One resample:
      * within the inoculated arm, draw 6 benches at random WITH replacement
        from the 6 inoculated benches;
      * within the uninoculated arm, do the same with the 6 uninoculated benches;
      * every seedling of a drawn bench comes along as an intact block, and a
        bench drawn twice contributes its fifteen seedlings twice;
      * recompute the difference in mean height between the two arms.

    Resampling is done separately within each arm so that every resample keeps
    the real design of 6 benches per arm.
    """
    rng = np.random.default_rng(seed)

    # Pre-split the heights into one array per bench, keyed by arm. Working with
    # these blocks is what makes "keep the whole bench together" literal.
    blocks = {}
    for arm in (TREATED, CONTROL):
        sub = df[df[GROUP] == arm]
        blocks[arm] = [
            sub.loc[sub[CLUSTER] == b, OUTCOME].to_numpy()
            for b in sorted(sub[CLUSTER].unique())
        ]

    n_treated_benches = len(blocks[TREATED])
    n_control_benches = len(blocks[CONTROL])

    diffs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        pick_t = rng.integers(0, n_treated_benches, size=n_treated_benches)
        pick_c = rng.integers(0, n_control_benches, size=n_control_benches)

        heights_t = np.concatenate([blocks[TREATED][j] for j in pick_t])
        heights_c = np.concatenate([blocks[CONTROL][j] for j in pick_c])

        diffs[i] = heights_t.mean() - heights_c.mean()

    return diffs, n_treated_benches, n_control_benches


def percentile_ci(diffs, level=CI_LEVEL):
    alpha = 1.0 - level
    lo = float(np.percentile(diffs, 100 * alpha / 2.0))
    hi = float(np.percentile(diffs, 100 * (1.0 - alpha / 2.0)))
    return lo, hi


def bootstrap_p_value(diffs, observed):
    """Two-sided resampling p-value read off the same bootstrap distribution.

    The bootstrap distribution is centred on the observed difference, so it
    describes sampling variation, not a null world. Shifting it to be centred on
    zero turns it into a reference distribution for "no treatment difference"
    that carries the same bench-level variability. The p-value is the share of
    shifted resamples at least as far from zero as the observed difference is.

    The (count + 1) / (B + 1) form keeps the p-value away from an exact zero,
    which the finite number of resamples cannot support: with B = 10000 the
    smallest reportable value is 1 / 10001.
    """
    centred = diffs - diffs.mean()
    count = int(np.sum(np.abs(centred) >= abs(observed)))
    return (count + 1.0) / (len(diffs) + 1.0), count


def naive_seedling_test(df):
    """ILLUSTRATIVE CONTRAST ONLY - not a valid inference for this design.

    Treats each of the 180 seedlings as an independent observation, which they
    are not, and therefore overstates the amount of information available.
    """
    h_t = df.loc[df[GROUP] == TREATED, OUTCOME].to_numpy()
    h_c = df.loc[df[GROUP] == CONTROL, OUTCOME].to_numpy()
    result = stats.ttest_ind(h_t, h_c, equal_var=False)
    return result, len(h_t), len(h_c)


def main():
    df = load_data()
    benches = bench_table(df)

    print("=" * 72)
    print("Scots pine nursery inoculant trial - height analysis")
    print("=" * 72)
    print()
    print("Data: {} seedling rows, {} benches, {} seedlings per bench.".format(
        len(df), df[CLUSTER].nunique(), int(benches["nSeedlings"].unique()[0])
    ))
    print()

    print("--- Bench-level summary (the bench is the experimental unit) ---")
    print(benches.to_string(index=False, float_format=lambda v: "{:.2f}".format(v)))
    print()

    print("--- Seedling-level summary by treatment ---")
    summary = (
        df.groupby(GROUP)[OUTCOME]
        .agg(nSeedlings="size", meanHeightCm="mean", sdHeightCm="std")
        .reset_index()
    )
    summary["nBenches"] = summary[GROUP].map(
        df.groupby(GROUP)[CLUSTER].nunique()
    )
    print(summary.to_string(index=False, float_format=lambda v: "{:.3f}".format(v)))
    print()

    # Between-bench spread of bench mean heights, within each arm.
    print("--- Spread of bench mean heights within each arm ---")
    for arm in (TREATED, CONTROL):
        means = benches.loc[benches[GROUP] == arm, "meanHeightCm"].to_numpy()
        print("  {:<13} bench means: {}".format(
            arm, ", ".join("{:.2f}".format(m) for m in sorted(means))
        ))
        print("  {:<13} SD of bench means = {:.3f} cm".format(arm, means.std(ddof=1)))
    print()

    obs_diff, mean_t, mean_c = observed_difference(df)
    print("--- Observed difference ---")
    print("  mean height, {:<13} = {:.3f} cm".format(TREATED, mean_t))
    print("  mean height, {:<13} = {:.3f} cm".format(CONTROL, mean_c))
    print("  difference (inoculated - uninoculated) = {:.3f} cm".format(obs_diff))
    print()

    print("--- PRIMARY INFERENCE: cluster (bench) bootstrap ---")
    diffs, n_bt, n_bc = cluster_bootstrap(df)
    lo, hi = percentile_ci(diffs)
    p_boot, n_extreme = bootstrap_p_value(diffs, obs_diff)

    print("  resamples: {:,} (seed {})".format(N_RESAMPLES, SEED))
    print("  benches drawn with replacement per resample: {} inoculated, {} uninoculated".format(
        n_bt, n_bc
    ))
    print("  bootstrap mean of the difference   = {:.3f} cm".format(diffs.mean()))
    print("  bootstrap SE of the difference     = {:.3f} cm".format(diffs.std(ddof=1)))
    print("  {:.0f}% percentile CI               = [{:.3f}, {:.3f}] cm".format(
        100 * CI_LEVEL, lo, hi
    ))
    print("  two-sided resampling p-value       = {:.4f}  ({} of {} centred resamples "
          "at least as extreme)".format(p_boot, n_extreme, N_RESAMPLES))
    print()

    print("--- ILLUSTRATIVE CONTRAST ONLY (NOT VALID FOR INFERENCE) ---")
    t_res, n_t, n_c = naive_seedling_test(df)
    print("  Welch two-sample t-test across all individual seedling rows")
    print("  ({} vs {} seedlings, treated as if independent):".format(n_t, n_c))
    print("    t = {:.3f}, p = {:.3e}".format(t_res.statistic, t_res.pvalue))
    print("  This test counts 180 seedlings as 180 independent observations.")
    print("  There are only 12 independent units (benches). It is shown for")
    print("  contrast with the bench-level result and must not be used to")
    print("  support any conclusion about the inoculant.")
    print()

    print("=" * 72)
    print("Primary result: difference = {:.2f} cm, {:.0f}% CI [{:.2f}, {:.2f}] cm, "
          "p = {:.4f}".format(obs_diff, 100 * CI_LEVEL, lo, hi, p_boot))
    print("=" * 72)


if __name__ == "__main__":
    main()
