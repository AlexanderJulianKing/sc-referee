"""
Prescribed burning and termite-mound soil nitrogen.

Primary inference: a self-written cluster (mound-level) bootstrap. Whole mounds are
drawn with replacement -- never individual cores -- so the resampling respects the
fact that the mound, not the core, is the independent unit of the study.

An ordinary two-sample t-test over all 112 core rows is also computed, but only as an
illustrative contrast. It is NOT a valid inference for this design.

Run:  python3 analysis.py
"""

import numpy as np
import pandas as pd
from scipy import stats

CSV = "termite_mound_soil_nitrogen.csv"
OUTCOME = "total_nitrogen_pct"
GROUP = "burn_block"
CLUSTER = "mound_id"
LEVEL_A = "burned"      # effect is reported as burned minus unburned
LEVEL_B = "unburned"

N_BOOT = 10000
SEED = 20260823
CI_LEVEL = 0.95


def load():
    df = pd.read_csv(CSV)
    assert df[OUTCOME].notna().all(), "missing outcome values"
    # The mound is the independent unit: check the structure the design claims.
    sizes = df.groupby(CLUSTER).size()
    assert (sizes == 8).all(), "expected exactly 8 cores per mound"
    labels = df.groupby(CLUSTER)[GROUP].nunique()
    assert (labels == 1).all(), "a mound must carry exactly one burn_block label"
    return df


def mound_table(df):
    """Collapse cores to the independent unit: one row per mound."""
    t = (df.groupby([CLUSTER, GROUP], as_index=False)
           .agg(n_cores=(OUTCOME, "size"), mound_mean=(OUTCOME, "mean")))
    return t.sort_values(CLUSTER).reset_index(drop=True)


def core_matrix(df, mounds):
    """(n_mounds x 8) matrix of core nitrogen values, rows ordered like `mounds`."""
    rows = [df.loc[df[CLUSTER] == m, OUTCOME].to_numpy() for m in mounds]
    return np.vstack(rows)


def cluster_bootstrap(mat_a, mat_b, rng, n_boot):
    """
    Draw whole mounds with replacement, separately within each burn block, keeping
    the number of mounds per block equal to the number observed (7 and 7). For each
    replicate the group mean is recomputed by pooling every core of every drawn
    mound, then the burned-minus-unburned difference is stored.
    """
    ka, kb = mat_a.shape[0], mat_b.shape[0]
    ia = rng.integers(0, ka, size=(n_boot, ka))
    ib = rng.integers(0, kb, size=(n_boot, kb))
    draw_a = mat_a[ia].reshape(n_boot, -1).mean(axis=1)
    draw_b = mat_b[ib].reshape(n_boot, -1).mean(axis=1)
    return draw_a - draw_b


def main():
    df = load()
    n_cores = len(df)
    mt = mound_table(df)
    n_mounds = len(mt)

    ids_a = mt.loc[mt[GROUP] == LEVEL_A, CLUSTER].tolist()
    ids_b = mt.loc[mt[GROUP] == LEVEL_B, CLUSTER].tolist()
    mat_a = core_matrix(df, ids_a)
    mat_b = core_matrix(df, ids_b)

    mean_a = mat_a.mean()
    mean_b = mat_b.mean()
    effect = mean_a - mean_b

    mm_a = mat_a.mean(axis=1)
    mm_b = mat_b.mean(axis=1)

    rng = np.random.default_rng(SEED)

    # --- Interval: bootstrap the effect itself --------------------------------
    boot = cluster_bootstrap(mat_a, mat_b, rng, N_BOOT)
    alpha = 1.0 - CI_LEVEL
    lo, hi = np.percentile(boot, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    se = boot.std(ddof=1)

    # --- p-value: bootstrap under the null of no block difference -------------
    # Centre each block's mounds on their own block mean, so the two blocks share a
    # common mean by construction, then repeat the identical whole-mound resampling.
    null_a = mat_a - mm_a.mean()
    null_b = mat_b - mm_b.mean()
    boot0 = cluster_bootstrap(null_a, null_b, rng, N_BOOT)
    n_extreme = int(np.sum(np.abs(boot0) >= abs(effect)))
    p_boot = (1 + n_extreme) / (N_BOOT + 1)

    # --- Illustrative contrast only: NOT a valid inference here ---------------
    a_rows = df.loc[df[GROUP] == LEVEL_A, OUTCOME].to_numpy()
    b_rows = df.loc[df[GROUP] == LEVEL_B, OUTCOME].to_numpy()
    t_stat, p_naive = stats.ttest_ind(a_rows, b_rows, equal_var=False)
    se_naive = np.sqrt(a_rows.var(ddof=1) / a_rows.size + b_rows.var(ddof=1) / b_rows.size)

    w = 78
    print("=" * w)
    print("Prescribed burning and termite-mound soil nitrogen")
    print("=" * w)
    print(f"Mounds (independent units): {n_mounds}   "
          f"({LEVEL_A}: {len(ids_a)}, {LEVEL_B}: {len(ids_b)})")
    print(f"Soil cores (rows):          {n_cores}   "
          f"({LEVEL_A}: {a_rows.size}, {LEVEL_B}: {b_rows.size})")
    print(f"Cores per mound:            8 (balanced)")
    print()
    print("Mound-level means of total_nitrogen_pct")
    for gid, mm in ((LEVEL_A, mm_a), (LEVEL_B, mm_b)):
        print(f"  {gid:<9} mean {mm.mean():.4f}   sd across mounds {mm.std(ddof=1):.4f}"
              f"   range {mm.min():.4f}-{mm.max():.4f}")
    print()

    print("-" * w)
    print("PRIMARY (dependence-aware): cluster bootstrap over whole mounds")
    print("-" * w)
    print(f"  Resampling unit        : mound (all 8 of its cores travel together)")
    print(f"  Replicates             : {N_BOOT}   RNG seed: {SEED}")
    print(f"  Effect ({LEVEL_A} - {LEVEL_B}) : {effect:+.4f} percent nitrogen by mass")
    print(f"  Bootstrap SE           : {se:.4f}")
    print(f"  {int(CI_LEVEL * 100)}% percentile CI      : [{lo:+.4f}, {hi:+.4f}]")
    print(f"  Bootstrap p-value      : {p_boot:.4f}  "
          f"({n_extreme} of {N_BOOT} null replicates at least as extreme)")
    print()

    print("-" * w)
    print("ILLUSTRATIVE CONTRAST ONLY -- NOT A VALID INFERENCE FOR THIS DESIGN")
    print("-" * w)
    print(f"  Plain two-sample Welch t-test over all {n_cores} core rows")
    print(f"  Effect ({LEVEL_A} - {LEVEL_B}) : {effect:+.4f}")
    print(f"  Naive SE               : {se_naive:.4f}")
    print(f"  t = {t_stat:.3f}   p = {p_naive:.3g}")
    print()
    print("  WARNING: this row-level comparison is NOT a valid inference for this")
    print("  design. It treats the 8 correlated cores from each mound as 8")
    print("  independent observations, so it claims 112 independent units when the")
    print("  study has only 14. Its standard error is understated and its p-value")
    print("  is anti-conservative. It is shown for contrast alone.")
    print(f"  The dependence-aware cluster bootstrap above (p = {p_boot:.4f}, "
          f"{int(CI_LEVEL * 100)}% CI")
    print(f"  [{lo:+.4f}, {hi:+.4f}]) is the study's conclusion.")
    print(f"  The naive SE is only {se_naive / se:.2f} times the cluster-bootstrap SE,")
    print(f"  i.e. the honest SE is {se / se_naive:.2f} times larger than the naive one.")
    print("=" * w)


if __name__ == "__main__":
    main()
