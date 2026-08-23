"""Artificial reef module design and fish abundance.

Primary inference: a hand-written cluster bootstrap that resamples whole reef
modules with replacement, keeping all five surveys of a drawn module together.
The module is the independent experimental unit (16 modules, 8 per design); the
80 survey rows are repeat visits and are not independent of one another.

Also reported, for illustration only, is a plain independent two-sample t-test
across all 80 survey rows. That row-level test is NOT a valid basis for
inference here.

Reads reef_fish_surveys.csv (committed as plain text). Does not regenerate data.
"""

import numpy as np
import pandas as pd
from scipy import stats

CSV = "reef_fish_surveys.csv"
SEED = 20260823
N_BOOT = 20000
GROUPS = ("complex_high_relief", "simple_block")  # contrast is complex - simple


def load():
    df = pd.read_csv(CSV)
    expected = ["module_id", "reef_design", "survey_number", "fish_count"]
    assert list(df.columns) == expected, df.columns
    assert len(df) == 80, len(df)
    assert df["fish_count"].notna().all()
    assert (df["fish_count"] >= 0).all()
    # every module sits in exactly one design and has all five surveys
    per_module = df.groupby("module_id").agg(
        n=("fish_count", "size"), n_design=("reef_design", "nunique")
    )
    assert (per_module["n"] == 5).all()
    assert (per_module["n_design"] == 1).all()
    return df


def module_table(df):
    """One row per module: the independent unit, with its mean fish count."""
    mod = (
        df.groupby(["module_id", "reef_design"], as_index=False)["fish_count"]
        .mean()
        .rename(columns={"fish_count": "module_mean_fish"})
        .sort_values("module_id")
        .reset_index(drop=True)
    )
    return mod


def contrast(mod):
    """Difference in mean fish per survey, complex minus simple, module-weighted."""
    a = mod.loc[mod["reef_design"] == GROUPS[0], "module_mean_fish"].to_numpy()
    b = mod.loc[mod["reef_design"] == GROUPS[1], "module_mean_fish"].to_numpy()
    return a.mean() - b.mean()


def cluster_bootstrap(mod, n_boot=N_BOOT, seed=SEED):
    """Resample whole modules with replacement, separately within each design.

    Drawing a module carries all five of that module's surveys with it, because
    the module mean is the module's whole contribution. Returns the bootstrap
    replicates of the complex-minus-simple difference.
    """
    rng = np.random.default_rng(seed)
    a = mod.loc[mod["reef_design"] == GROUPS[0], "module_mean_fish"].to_numpy()
    b = mod.loc[mod["reef_design"] == GROUPS[1], "module_mean_fish"].to_numpy()
    na, nb = len(a), len(b)
    ia = rng.integers(0, na, size=(n_boot, na))
    ib = rng.integers(0, nb, size=(n_boot, nb))
    return a[ia].mean(axis=1) - b[ib].mean(axis=1)


def main():
    df = load()
    mod = module_table(df)

    n_modules = mod["module_id"].nunique()
    n_rows = len(df)
    counts = mod.groupby("reef_design").size()

    obs = contrast(mod)
    reps = cluster_bootstrap(mod)

    boot_se = reps.std(ddof=1)
    lo, hi = np.percentile(reps, [2.5, 97.5])

    # Two-sided p-value: recentre the bootstrap replicates on zero to get a null
    # distribution for the difference, then ask how often a null replicate is at
    # least as far from zero as the observed difference. The (r+1)/(B+1) form
    # keeps the p-value away from an impossible exact zero.
    null = reps - obs
    r = int(np.sum(np.abs(null) >= abs(obs)))
    p_boot = (r + 1) / (N_BOOT + 1)
    z_like = obs / boot_se

    # Illustration only, not valid inference here.
    row_a = df.loc[df["reef_design"] == GROUPS[0], "fish_count"].to_numpy()
    row_b = df.loc[df["reef_design"] == GROUPS[1], "fish_count"].to_numpy()
    t_row, p_row = stats.ttest_ind(row_a, row_b, equal_var=False)
    welch_df = (
        (row_a.var(ddof=1) / len(row_a) + row_b.var(ddof=1) / len(row_b)) ** 2
        / (
            (row_a.var(ddof=1) / len(row_a)) ** 2 / (len(row_a) - 1)
            + (row_b.var(ddof=1) / len(row_b)) ** 2 / (len(row_b) - 1)
        )
    )

    print("=" * 72)
    print("ARTIFICIAL REEF DESIGN AND FISH ABUNDANCE")
    print("=" * 72)
    print()
    print("Data: %s" % CSV)
    print("  survey rows                    : %d" % n_rows)
    print("  reef modules (independent units): %d" % n_modules)
    print("  modules per design             : %s = %d, %s = %d"
          % (GROUPS[0], counts[GROUPS[0]], GROUPS[1], counts[GROUPS[1]]))
    print("  surveys per module             : 5")
    print()

    print("Module-level summary (mean fish per survey, one value per module):")
    for design in GROUPS:
        v = mod.loc[mod["reef_design"] == design, "module_mean_fish"].to_numpy()
        print("  %-20s n=%d  mean=%6.2f  sd=%5.2f  range %.1f to %.1f"
              % (design, len(v), v.mean(), v.std(ddof=1), v.min(), v.max()))
    print()
    print("  Per-module means:")
    for _, row in mod.iterrows():
        print("    %-6s %-20s %6.2f"
              % (row["module_id"], row["reef_design"], row["module_mean_fish"]))
    print()

    print("-" * 72)
    print("PRIMARY RESULT - cluster bootstrap over whole modules")
    print("-" * 72)
    print("  Resamples                : %d" % N_BOOT)
    print("  Random seed              : %d" % SEED)
    print("  Resampling unit          : the reef module; a drawn module brings")
    print("                             all five of its surveys with it.")
    print("  Independent units        : %d modules (%d per design), not %d rows."
          % (n_modules, counts[GROUPS[0]], n_rows))
    print()
    print("  Difference (complex_high_relief - simple_block): %+.2f fish per survey"
          % obs)
    print("  Bootstrap standard error : %.2f" % boot_se)
    print("  Test statistic (difference / bootstrap SE): %+.3f" % z_like)
    print("  95%% percentile CI        : (%+.2f, %+.2f) fish per survey" % (lo, hi))
    print("  Two-sided bootstrap p    : %.4f  (%d of %d recentred replicates"
          % (p_boot, r, N_BOOT))
    print("                             at least as extreme as observed)")
    print()

    print("-" * 72)
    print("ILLUSTRATION ONLY - NOT A VALID BASIS FOR INFERENCE HERE")
    print("-" * 72)
    print("  Plain independent two-sample t-test (Welch) across all %d survey rows,"
          % n_rows)
    print("  treating every row as if it were its own independent observation:")
    print("    t = %+.3f, df = %.1f, p = %.3e (n = %d rows, %d per design)"
          % (t_row, welch_df, p_row, n_rows, len(row_a)))
    print()
    print("  This row-level p-value is shown only for illustration. It is not a")
    print("  valid basis for inference in this study, because it counts the five")
    print("  repeat surveys of the same module as five independent data points.")
    print("  The five surveys of one module are repeat visits to the same patch of")
    print("  reef, so they are correlated. Treating them as independent inflates")
    print("  the apparent sample size from %d modules to %d rows and makes the"
          % (n_modules, n_rows))
    print("  p-value far smaller than the evidence supports. The module-level")
    print("  bootstrap above is the result to read.")
    print()
    print("  Row-level p is smaller than the module-level p by a factor of about %.0f."
          % (p_boot / p_row))
    print("=" * 72)


if __name__ == "__main__":
    main()
