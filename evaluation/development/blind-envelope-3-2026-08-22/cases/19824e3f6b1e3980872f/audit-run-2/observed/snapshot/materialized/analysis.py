"""
Total phosphorus and catchment land use: 16-lake limnology survey.

Design
------
Sixteen lakes were surveyed, eight with predominantly agricultural catchments and
eight with predominantly forested catchments. Six open-water stations were sampled
in each lake, giving 96 water samples. Catchment land use is a property of the lake,
so the lake, not the water sample, is the independent unit. The six rows that share
a `lake_id` are spatial subsamples of the same lake and are not independent of one
another.

Primary inference
-----------------
A hand-written lake-level resampling procedure. Whole lakes are the resampling unit
throughout, never individual water samples:

  * Null distribution: exact permutation of the eight land-use labels over the 16
    lakes. All C(16, 8) = 12870 assignments are enumerated, so the p-value is exact
    and needs no random number generator.
  * Interval: a cluster bootstrap that resamples whole lakes with replacement within
    each group and rebuilds the group means from the resampled lakes.

No mixed-model or GEE library is used; the dependence is handled by the resampling
scheme itself.

Illustrative contrast (NOT the inferential result)
--------------------------------------------------
A plain two-sample Welch t-test across all 96 individual samples is also computed and
printed in its own clearly marked block. It treats the 96 samples as 96 independent
observations, which they are not, and it is reported only to show what that mistake
would look like here. It is not a valid basis for inference in this survey.

Run with:  /usr/local/bin/python3 analysis.py
"""

import os
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = "lake_phosphorus.csv"
RESPONSE = "total_phosphorus_ug_l"
GROUP = "catchment_land_use"
CLUSTER = "lake_id"
LEVEL_A = "agricultural"
LEVEL_B = "forested"

N_BOOT = 20000
BOOT_SEED = 20260822
CI_LEVEL = 0.95


def rule(char="=", width=78):
    return char * width


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    df = pd.read_csv(path)
    expected = [
        "lake_id",
        "catchment_land_use",
        "station_number",
        "total_phosphorus_ug_l",
        "water_depth_m",
        "lake_area_ha",
    ]
    assert list(df.columns) == expected, f"unexpected columns: {list(df.columns)}"
    assert df.notna().all().all(), "missing values present"
    assert set(df[GROUP].unique()) == {LEVEL_A, LEVEL_B}, "unexpected group levels"
    # Land use and lake area must be constant within a lake.
    for col in (GROUP, "lake_area_ha"):
        assert (df.groupby(CLUSTER)[col].nunique() == 1).all(), f"{col} varies within a lake"
    return df


def describe_design(df):
    print(rule())
    print("SURVEY DESIGN AND SAMPLE SIZE")
    print(rule())
    n_lakes = df[CLUSTER].nunique()
    n_rows = len(df)
    per_lake = df.groupby(CLUSTER).size()
    print(f"Independent unit          : lake (column '{CLUSTER}')")
    print(f"Row                       : one water sample from one station in one lake")
    print(f"Sample size               : {n_lakes} lakes contributing {n_rows} samples")
    print(f"Stations per lake         : {per_lake.min()}-{per_lake.max()} "
          f"(balanced: {bool(per_lake.nunique() == 1)})")
    lakes_per_group = df.groupby(GROUP)[CLUSTER].nunique()
    rows_per_group = df.groupby(GROUP).size()
    for level in (LEVEL_A, LEVEL_B):
        print(f"  {level:<14}: {lakes_per_group[level]} lakes, {rows_per_group[level]} samples")
    print()


def describe_response(df, lake_means):
    print(rule())
    print("DESCRIPTIVE SUMMARY OF TOTAL PHOSPHORUS (ug/L)")
    print(rule())
    print("Individual water samples (n = 96), descriptive only:")
    for level in (LEVEL_A, LEVEL_B):
        v = df.loc[df[GROUP] == level, RESPONSE]
        print(f"  {level:<14}: n={len(v):3d}  mean={v.mean():6.2f}  sd={v.std(ddof=1):5.2f}  "
              f"median={v.median():6.2f}  min={v.min():5.1f}  max={v.max():5.1f}")
    print()
    print("Lake means (n = 16 lakes), the unit the primary inference uses:")
    for level in (LEVEL_A, LEVEL_B):
        v = lake_means.loc[lake_means[GROUP] == level, RESPONSE]
        print(f"  {level:<14}: n={len(v):3d}  mean={v.mean():6.2f}  sd={v.std(ddof=1):5.2f}  "
              f"median={v.median():6.2f}  min={v.min():5.1f}  max={v.max():5.1f}")
    print()


def variance_components(df):
    """One-way random-effects components for lakes nested in land use.

    Land-use group means are removed first (fixed effect), then the remaining
    variation is split between lakes and between stations within a lake.
    Balanced design, so the classic ANOVA estimator applies directly.
    """
    n_per_lake = int(df.groupby(CLUSTER).size().iloc[0])
    n_lakes = df[CLUSTER].nunique()
    n_groups = df[GROUP].nunique()

    lake_mean = df.groupby(CLUSTER)[RESPONSE].transform("mean")
    group_mean = df.groupby(GROUP)[RESPONSE].transform("mean")

    ss_within = float(((df[RESPONSE] - lake_mean) ** 2).sum())
    ss_between = float(((lake_mean - group_mean) ** 2).sum())

    df_within = len(df) - n_lakes
    df_between = n_lakes - n_groups

    ms_within = ss_within / df_within
    ms_between = ss_between / df_between
    var_between = max((ms_between - ms_within) / n_per_lake, 0.0)
    var_within = ms_within
    icc = var_between / (var_between + var_within)

    print(rule())
    print("WHY THE SAMPLES INSIDE A LAKE CANNOT BE TREATED AS INDEPENDENT")
    print(rule())
    print(f"Between-lake SD (within land use) : {np.sqrt(var_between):5.2f} ug/L")
    print(f"Within-lake (station-to-station) SD: {np.sqrt(var_within):5.2f} ug/L")
    print(f"Intraclass correlation (ICC)       : {icc:5.3f}")
    print("Two samples from the same lake are far more alike than two samples from")
    print("different lakes in the same land-use group, so the 96 samples carry much")
    print("less information than 96 independent observations would.")
    print()
    return {"sd_between": float(np.sqrt(var_between)),
            "sd_within": float(np.sqrt(var_within)),
            "icc": float(icc)}


def lake_level_table(df):
    lm = (df.groupby([CLUSTER, GROUP], as_index=False)
            .agg(**{RESPONSE: (RESPONSE, "mean"),
                    "n_stations": (RESPONSE, "size")}))
    return lm


def exact_permutation_test(values_a, values_b):
    """Exact permutation test on lake means, permuting land-use labels over lakes.

    The resampling unit is the whole lake. Every one of the C(n, n_a) ways of
    assigning the agricultural label to lakes is enumerated, so no random draws
    are involved and the p-value is exact for this design.
    """
    pooled = np.concatenate([values_a, values_b])
    n = pooled.size
    n_a = values_a.size
    observed = values_a.mean() - values_b.mean()
    total = pooled.sum()

    diffs = np.empty(0)
    idx = np.arange(n)
    all_combos = list(combinations(idx, n_a))
    diffs = np.empty(len(all_combos))
    for i, combo in enumerate(all_combos):
        sa = pooled[list(combo)].sum()
        diffs[i] = sa / n_a - (total - sa) / (n - n_a)

    tol = 1e-9
    p_two = float(np.mean(np.abs(diffs) >= abs(observed) - tol))
    return {"observed": float(observed),
            "n_permutations": len(all_combos),
            "p_two_sided": p_two,
            "null_diffs": diffs}


def cluster_bootstrap_ci(values_a, values_b, n_boot=N_BOOT, seed=BOOT_SEED, level=CI_LEVEL):
    """Percentile CI from resampling whole lakes with replacement within each group."""
    rng = np.random.default_rng(seed)
    n_a, n_b = values_a.size, values_b.size
    ia = rng.integers(0, n_a, size=(n_boot, n_a))
    ib = rng.integers(0, n_b, size=(n_boot, n_b))
    boot = values_a[ia].mean(axis=1) - values_b[ib].mean(axis=1)
    alpha = 1.0 - level
    lo, hi = np.percentile(boot, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"lo": float(lo), "hi": float(hi), "se": float(boot.std(ddof=1)),
            "n_boot": n_boot, "level": level, "boot": boot}


def primary_analysis(lake_means, n_rows):
    a = lake_means.loc[lake_means[GROUP] == LEVEL_A, RESPONSE].to_numpy(float)
    b = lake_means.loc[lake_means[GROUP] == LEVEL_B, RESPONSE].to_numpy(float)

    perm = exact_permutation_test(a, b)
    boot = cluster_bootstrap_ci(a, b)

    print(rule())
    print("PRIMARY RESULT (dependence-aware: whole lakes are the resampling unit)")
    print(rule())
    print(f"Sample size                    : {a.size + b.size} lakes contributing "
          f"{n_rows} samples")
    print(f"Mean of lake means, {LEVEL_A:<12}: {a.mean():6.2f} ug/L (n = {a.size} lakes)")
    print(f"Mean of lake means, {LEVEL_B:<12}: {b.mean():6.2f} ug/L (n = {b.size} lakes)")
    print(f"Difference (agri - forest)     : {perm['observed']:6.2f} ug/L")
    print()
    print(f"Exact lake-level permutation test over all {perm['n_permutations']} "
          f"label assignments:")
    print(f"  two-sided p                  : {perm['p_two_sided']:.6f}")
    print(f"  smallest attainable p        : {2.0 / perm['n_permutations']:.6f}")
    print()
    print(f"Cluster bootstrap, {boot['n_boot']} resamples of whole lakes "
          f"(seed {BOOT_SEED}):")
    print(f"  bootstrap SE of difference   : {boot['se']:6.2f} ug/L")
    print(f"  {int(boot['level'] * 100)}% percentile interval     : "
          f"[{boot['lo']:.2f}, {boot['hi']:.2f}] ug/L")
    print()
    return perm, boot


def illustrative_row_level_contrast(df):
    a = df.loc[df[GROUP] == LEVEL_A, RESPONSE].to_numpy(float)
    b = df.loc[df[GROUP] == LEVEL_B, RESPONSE].to_numpy(float)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    dfree = (a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) ** 2 / (
        (a.var(ddof=1) / a.size) ** 2 / (a.size - 1)
        + (b.var(ddof=1) / b.size) ** 2 / (b.size - 1))

    print(rule("*"))
    print("ILLUSTRATIVE CONTRAST ONLY - NOT THE INFERENTIAL RESULT")
    print(rule("*"))
    print("The block below treats all 96 water samples as if they were 96 independent")
    print("observations. They are not: six samples share each lake, and land use is")
    print("assigned at the lake, not at the station. This test is printed only to show")
    print("what that error produces here. Do not read it as evidence about the")
    print("difference between agricultural and forested catchments.")
    print()
    print(f"  Welch two-sample t-test on individual samples (n = {a.size} vs {b.size}):")
    print(f"    mean difference            : {a.mean() - b.mean():6.2f} ug/L")
    print(f"    t                          : {t:7.3f}")
    print(f"    approximate df             : {dfree:7.2f}")
    print(f"    two-sided p                : {p:.3e}")
    print()
    print(f"  It spends about {dfree:.0f} degrees of freedom where the design supplies")
    print("  14 (16 lakes, two group means estimated), so its p-value is far too small")
    print("  and any interval built from it far too narrow. The valid answer is the")
    print("  primary result above.")
    print(rule("*"))
    print()
    return {"t": float(t), "p": float(p), "df": float(dfree),
            "diff": float(a.mean() - b.mean())}


def main():
    df = load_data()
    describe_design(df)

    lake_means = lake_level_table(df)
    describe_response(df, lake_means)
    variance_components(df)

    primary_analysis(lake_means, len(df))
    illustrative_row_level_contrast(df)

    print(rule())
    print("Reminder: the primary result is the lake-level resampling analysis.")
    print("The row-level t-test above is illustrative and is not valid inference here.")
    print(rule())


if __name__ == "__main__":
    main()
