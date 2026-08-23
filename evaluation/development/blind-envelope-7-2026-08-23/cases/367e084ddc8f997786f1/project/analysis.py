"""Cistern faecal indicator study: roof catchment material comparison.

Reads the committed CSV of assay replicate measurements and compares
log10 faecal indicator gene concentration between coated-metal and
asphalt-shingle roof catchments with an independent two-sample t-test.
Every assay replicate in the table is one observation in the test.
"""

import os

import pandas as pd
from scipy import stats

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cistern_faecal_indicator.csv")

OUTCOME = "log10_gene_copies_per_100ml"
GROUP = "roof_catchment_material"
GROUP_LEVELS = ["coated_metal", "asphalt_shingle"]


def load_data(path=DATA_FILE):
    """Load the committed assay replicate table."""
    df = pd.read_csv(path)
    missing = [c for c in ("cistern_id", GROUP, "assay_replicate", OUTCOME)
               if c not in df.columns]
    if missing:
        raise ValueError("missing expected columns: %s" % ", ".join(missing))
    return df


def group_summary(df):
    """Sample size, mean and standard deviation for each roof material."""
    summary = (df.groupby(GROUP)[OUTCOME]
                 .agg(n="size", mean="mean", sd="std")
                 .reindex(GROUP_LEVELS))
    return summary


def two_sample_test(df):
    """Independent two-sample t-test on all assay replicates."""
    metal = df.loc[df[GROUP] == "coated_metal", OUTCOME]
    shingle = df.loc[df[GROUP] == "asphalt_shingle", OUTCOME]
    t_stat, p_value = stats.ttest_ind(shingle, metal)
    dof = len(shingle) + len(metal) - 2
    return t_stat, p_value, dof, metal, shingle


def main():
    df = load_data()

    print("Rows loaded: %d" % len(df))
    print("Cisterns: %d" % df["cistern_id"].nunique())
    print("Assay replicates per cistern: %d"
          % int(df.groupby("cistern_id").size().unique()[0]))
    print()

    summary = group_summary(df)
    print("Group summaries (log10 gene copies per 100 mL)")
    for level, row in summary.iterrows():
        print("  %-16s n = %2d   mean = %.3f   sd = %.3f"
              % (level, int(row["n"]), row["mean"], row["sd"]))
    print()

    t_stat, p_value, dof, metal, shingle = two_sample_test(df)
    diff = shingle.mean() - metal.mean()

    print("Independent two-sample t-test (asphalt_shingle vs coated_metal)")
    print("  n (asphalt_shingle) = %d assay measurements" % len(shingle))
    print("  n (coated_metal)    = %d assay measurements" % len(metal))
    print("  mean difference     = %.3f log10 copies per 100 mL" % diff)
    print("  t(%d) = %.3f" % (dof, t_stat))
    print("  p = %.3g" % p_value)


if __name__ == "__main__":
    main()
