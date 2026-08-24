"""Blueberry inoculation trial: does a mycorrhizal inoculant change fruit sweetness?

The experimental unit is the bush. Five berry clusters were picked from each of
24 potted highbush blueberry bushes and each cluster's juice was read on a
refractometer, so the raw file holds 120 cluster rows. The five clusters from a
bush are subsamples of that bush, not independent experimental units: treatment
was applied to the whole bush at planting, once per bush.

So the analysis proceeds in two steps.

  Step 1  Reduce each bush to a single number by averaging its five cluster
          readings. This collapses 120 cluster rows to 24 bush values.
  Step 2  Compare the two treatment groups using those 24 per-bush values only,
          n = 24 bushes, 12 per treatment.

Nothing downstream of step 1 touches the cluster rows again.

Run with:  python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "blueberry_brix_clusters.csv")

UNIT_COL = "bush_label"
GROUP_COL = "treatment"
SUBSAMPLE_COL = "cluster_number"
OUTCOME_COL = "soluble_solids_brix"

TREATED = "inoculated"
CONTROL = "uninoculated"

CLUSTERS_PER_BUSH = 5


def load_clusters(path):
    """Read the raw cluster-level table and check its shape."""
    clusters = pd.read_csv(path)

    expected = [UNIT_COL, GROUP_COL, SUBSAMPLE_COL, OUTCOME_COL]
    missing = [c for c in expected if c not in clusters.columns]
    if missing:
        raise ValueError("data file is missing columns: %s" % missing)

    if clusters[OUTCOME_COL].isna().any():
        raise ValueError("data file has missing Brix readings")

    # Treatment must be constant within a bush: it was applied to the bush.
    per_bush_levels = clusters.groupby(UNIT_COL)[GROUP_COL].nunique()
    if (per_bush_levels != 1).any():
        raise ValueError("a bush carries more than one treatment label")

    # Every bush should carry the same number of cluster subsamples.
    per_bush_counts = clusters.groupby(UNIT_COL)[OUTCOME_COL].size()
    if not (per_bush_counts == CLUSTERS_PER_BUSH).all():
        raise ValueError("not every bush has %d cluster readings" % CLUSTERS_PER_BUSH)

    return clusters


def summarise_variation(clusters):
    """Describe how much of the spread sits within a bush versus between bushes.

    This is descriptive context for the reader, not a test. The within-bush SD is
    pooled across bushes; the between-bush SD is the spread of the bush means
    after removing the treatment difference.
    """
    within = clusters.groupby(UNIT_COL)[OUTCOME_COL].std(ddof=1)
    pooled_within_sd = float(np.sqrt(np.mean(within.values ** 2)))

    bush_means = clusters.groupby([UNIT_COL, GROUP_COL], as_index=False)[OUTCOME_COL].mean()
    centred = bush_means[OUTCOME_COL] - bush_means.groupby(GROUP_COL)[OUTCOME_COL].transform("mean")
    between_bush_sd = float(centred.std(ddof=1))

    return pooled_within_sd, between_bush_sd


def reduce_to_bushes(clusters):
    """Step 1: average the five cluster readings on each bush.

    One row out per bush. From here on the cluster rows play no further part.
    """
    bushes = (
        clusters
        .groupby([UNIT_COL, GROUP_COL], as_index=False)
        .agg(
            mean_brix=(OUTCOME_COL, "mean"),
            n_clusters=(OUTCOME_COL, "size"),
        )
        .sort_values(UNIT_COL)
        .reset_index(drop=True)
    )
    return bushes


def compare_groups(bushes):
    """Step 2: two-group comparison on the per-bush means, 12 bushes per group."""
    treated = bushes.loc[bushes[GROUP_COL] == TREATED, "mean_brix"].to_numpy()
    control = bushes.loc[bushes[GROUP_COL] == CONTROL, "mean_brix"].to_numpy()

    if len(treated) == 0 or len(control) == 0:
        raise ValueError("one of the treatment groups is empty")

    # Welch's two-sample t test: does not assume the two groups share a variance.
    t_stat, p_value = stats.ttest_ind(treated, control, equal_var=False)

    diff = float(treated.mean() - control.mean())

    # Welch confidence interval for the difference in means.
    se = float(np.sqrt(treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)))
    df = se ** 4 / (
        (treated.var(ddof=1) / len(treated)) ** 2 / (len(treated) - 1)
        + (control.var(ddof=1) / len(control)) ** 2 / (len(control) - 1)
    )
    crit = stats.t.ppf(0.975, df)
    ci_low = diff - crit * se
    ci_high = diff + crit * se

    return {
        "n_treated": int(len(treated)),
        "n_control": int(len(control)),
        "mean_treated": float(treated.mean()),
        "mean_control": float(control.mean()),
        "sd_treated": float(treated.std(ddof=1)),
        "sd_control": float(control.std(ddof=1)),
        "difference": diff,
        "se": se,
        "df": float(df),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
    }


def main():
    clusters = load_clusters(DATA_FILE)

    print("=" * 68)
    print("Blueberry inoculation trial: soluble solids (degrees Brix)")
    print("=" * 68)
    print()

    print("Raw cluster-level file")
    print("  rows (one cluster reading each) : %d" % len(clusters))
    print("  bushes (experimental units)     : %d" % clusters[UNIT_COL].nunique())
    print("  clusters measured per bush      : %d" % CLUSTERS_PER_BUSH)
    print("  Brix range across all clusters  : %.1f to %.1f"
          % (clusters[OUTCOME_COL].min(), clusters[OUTCOME_COL].max()))
    print()

    pooled_within_sd, between_bush_sd = summarise_variation(clusters)
    print("Spread, for context")
    print("  SD between clusters on one bush (pooled) : %.3f Brix" % pooled_within_sd)
    print("  SD between bush means, within treatment  : %.3f Brix" % between_bush_sd)
    print()

    # ---- Step 1: clusters are subsamples, so average them up to the bush ----
    bushes = reduce_to_bushes(clusters)
    print("Step 1: averaged the %d clusters on each bush to one value per bush"
          % CLUSTERS_PER_BUSH)
    print("  bush-level rows now : %d" % len(bushes))
    print()
    print("Per-bush mean Brix")
    for _, row in bushes.iterrows():
        print("  %-6s  %-13s  %.3f  (mean of %d clusters)"
              % (row[UNIT_COL], row[GROUP_COL], row["mean_brix"], int(row["n_clusters"])))
    print()

    # ---- Step 2: compare the two treatment groups on the per-bush values ----
    result = compare_groups(bushes)
    print("Step 2: two-group comparison on the per-bush means")
    print("  sample size : %d bushes (%d inoculated, %d uninoculated)"
          % (result["n_treated"] + result["n_control"],
             result["n_treated"], result["n_control"]))
    print()
    print("  %-14s %7s %9s %9s" % ("group", "bushes", "mean", "SD"))
    print("  %-14s %7d %9.3f %9.3f"
          % (TREATED, result["n_treated"], result["mean_treated"], result["sd_treated"]))
    print("  %-14s %7d %9.3f %9.3f"
          % (CONTROL, result["n_control"], result["mean_control"], result["sd_control"]))
    print()
    print("  difference (inoculated - uninoculated) : %+.3f Brix" % result["difference"])
    print("  95%% confidence interval                : %+.3f to %+.3f Brix"
          % (result["ci_low"], result["ci_high"]))
    print("  Welch two-sample t test                : t = %.3f, df = %.2f, p = %.4f"
          % (result["t_stat"], result["df"], result["p_value"]))
    print()
    print("=" * 68)


if __name__ == "__main__":
    main()
