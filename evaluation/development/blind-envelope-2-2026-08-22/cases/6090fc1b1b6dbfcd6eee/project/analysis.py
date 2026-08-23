"""Restored versus channelised stream reaches: sensitive invertebrate richness.

The stream reach is the experimental unit. Restoration was applied along whole
reaches, so the twelve kick-net samples taken inside a reach are subsamples of
that reach and not independently treated sites.

Consequently:
  * the inferential two-group comparison is run on the per-reach summary file
    only (20 reach-level values, 10 per group);
  * the raw sample-level file is used for descriptive checks and counts only,
    and no group comparison is run on the raw rows.

Run with:  /usr/local/bin/python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "kicknet_samples_raw.csv")
SUMMARY_PATH = os.path.join(HERE, "reach_summary.csv")

EXPECTED_SAMPLES_PER_REACH = 12
GROUPS = ("restored", "channelised")


def rule(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main():
    raw = pd.read_csv(RAW_PATH)
    summary = pd.read_csv(SUMMARY_PATH)

    # ------------------------------------------------------------------
    # DESCRIPTIVE ONLY -- raw sample-level file.
    # Counts and consistency checks. No group comparison is performed here.
    # ------------------------------------------------------------------
    rule("DESCRIPTIVE ONLY -- raw kick-net sample file (no inference here)")

    print("Raw file: %s" % os.path.basename(RAW_PATH))
    print("Columns: %s" % ", ".join(raw.columns))
    print()

    total_samples = len(raw)
    print("DESCRIPTIVE: total kick-net samples ........... %d" % total_samples)

    per_group_samples = raw.groupby("restoration_group").size()
    for group in GROUPS:
        print("DESCRIPTIVE: kick-net samples, %-12s ... %d"
              % (group, int(per_group_samples[group])))

    n_reaches_raw = raw["reach_id"].nunique()
    print("DESCRIPTIVE: distinct reaches in raw file ..... %d" % n_reaches_raw)
    print()

    # Every reach contributed the expected number of samples.
    per_reach_counts = raw.groupby("reach_id").size()
    bad_counts = per_reach_counts[per_reach_counts != EXPECTED_SAMPLES_PER_REACH]
    print("DESCRIPTIVE: expected samples per reach ....... %d"
          % EXPECTED_SAMPLES_PER_REACH)
    print("DESCRIPTIVE: reaches with an unexpected count . %d" % len(bad_counts))
    if len(bad_counts):
        print(bad_counts.to_string())
    else:
        print("DESCRIPTIVE: all %d reaches contributed exactly %d samples."
              % (n_reaches_raw, EXPECTED_SAMPLES_PER_REACH))
    print()

    # n_samples in the summary file agrees with the raw row counts.
    n_samples_check = summary.set_index("reach_id")["n_samples"].sub(
        per_reach_counts, fill_value=-1)
    n_samples_mismatch = int((n_samples_check != 0).sum())
    print("DESCRIPTIVE: reaches where summary n_samples "
          "disagrees with raw row count ... %d" % n_samples_mismatch)

    # Each reach's summary mean matches the mean of its raw rows.
    raw_means = (raw.groupby("reach_id")["sensitive_taxa_count"]
                    .mean()
                    .round(2)
                    .rename("mean_from_raw"))
    check = summary.set_index("reach_id").join(raw_means)
    check["abs_diff"] = (check["mean_sensitive_taxa"]
                         - check["mean_from_raw"]).abs()
    mean_mismatch = int((check["abs_diff"] > 1e-9).sum())
    print("DESCRIPTIVE: reaches where summary mean "
          "disagrees with raw mean ........ %d" % mean_mismatch)
    print()
    print("DESCRIPTIVE: per-reach check table")
    print(check[["restoration_group", "n_samples", "mean_sensitive_taxa",
                 "mean_from_raw", "abs_diff"]].to_string())
    print()

    # Descriptive sample-level richness, reported as description only.
    print("DESCRIPTIVE: sample-level mean sensitive taxa by group "
          "(description only, not an inferential comparison)")
    desc = raw.groupby("restoration_group")["sensitive_taxa_count"].agg(
        ["size", "mean", "std", "min", "max"])
    print(desc.round(2).to_string())

    # ------------------------------------------------------------------
    # INFERENTIAL -- per-reach summary file only.
    # 20 reach-level values, 10 per group. The reach is the unit of analysis.
    # ------------------------------------------------------------------
    rule("INFERENTIAL -- per-reach comparison (unit of analysis = reach)")

    print("Summary file: %s" % os.path.basename(SUMMARY_PATH))
    print("Columns: %s" % ", ".join(summary.columns))
    print()

    restored = summary.loc[summary["restoration_group"] == "restored",
                           "mean_sensitive_taxa"]
    channelised = summary.loc[summary["restoration_group"] == "channelised",
                              "mean_sensitive_taxa"]

    n_restored = len(restored)
    n_channelised = len(channelised)
    n_total = n_restored + n_channelised

    mean_restored = restored.mean()
    mean_channelised = channelised.mean()
    sd_restored = restored.std(ddof=1)
    sd_channelised = channelised.std(ddof=1)
    difference = mean_restored - mean_channelised

    # Welch's independent two-sample t-test on the 20 reach-level values.
    t_stat, p_value = stats.ttest_ind(restored, channelised, equal_var=False)
    df_welch = (
        (sd_restored ** 2 / n_restored + sd_channelised ** 2 / n_channelised) ** 2
        / ((sd_restored ** 2 / n_restored) ** 2 / (n_restored - 1)
           + (sd_channelised ** 2 / n_channelised) ** 2 / (n_channelised - 1))
    )

    print("Sample size is counted in REACHES, not kick-net samples.")
    print("  n reaches, restored ....................... %d" % n_restored)
    print("  n reaches, channelised .................... %d" % n_channelised)
    print("  n reaches, total .......................... %d" % n_total)
    print()
    print("  mean sensitive taxa, restored ............. %.2f" % mean_restored)
    print("  mean sensitive taxa, channelised .......... %.2f" % mean_channelised)
    print("  SD of reach means, restored ............... %.2f" % sd_restored)
    print("  SD of reach means, channelised ............ %.2f" % sd_channelised)
    print("  difference in means (restored - channelised) %.2f" % difference)
    print()
    print("Independent two-sample t-test (Welch, unequal variances) on the "
          "%d reach means:" % n_total)
    print("  t ......................................... %.3f" % t_stat)
    print("  degrees of freedom ........................ %.2f" % df_welch)
    print("  p-value ................................... %.6g" % p_value)
    print()

    print("Note: no group comparison was run on the 240 raw kick-net rows. "
          "Those rows are subsamples within reaches and are reported above "
          "for description only.")


if __name__ == "__main__":
    main()
