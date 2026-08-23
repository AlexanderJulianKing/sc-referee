"""Organoid barrier function by tight-junction genotype.

Primary analysis: donor-level cluster bootstrap of the difference in mean day-7
TEER between carrier and non-carrier donors. The donor is the independent
experimental unit; the 6 wells of a donor are technical replicates and are kept
together whenever that donor is drawn.

Illustrative contrast only: a plain well-level two-sample t-test that wrongly
treats all 108 wells as independent observations.

Run with: /usr/local/bin/python3 analysis.py
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
CSV_NAME = "organoid_teer.csv"
OUTCOME = "teer_day7_ohm_cm2"
UNIT = "donor_id"
GROUP = "genotype"
REFERENCE_LEVEL = "non_carrier"
COMPARISON_LEVEL = "carrier"

N_RESAMPLES = 20000
SEED = 20260822
CI_LEVEL = 0.95


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_wells():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    wells = pd.read_csv(path)
    return wells


# ---------------------------------------------------------------------------
# Donor-level cluster bootstrap, written out by hand
# ---------------------------------------------------------------------------
def cluster_bootstrap(wells, n_resamples, seed, ci_level):
    """Resample whole donors with replacement inside each genotype group.

    Every time a donor is drawn, all of that donor's well measurements come
    along as one block, so the resampling unit is the donor and the correlation
    between a donor's wells is preserved. For each resample the difference in
    group means (comparison minus reference) is recomputed.

    This is built from ordinary array operations only: no library routine
    performs the resampling, the interval, or the test.
    """
    # Pack each donor's wells into its own array, grouped by genotype.
    donor_blocks = {REFERENCE_LEVEL: [], COMPARISON_LEVEL: []}
    donor_labels = {REFERENCE_LEVEL: [], COMPARISON_LEVEL: []}
    for donor, block in wells.groupby(UNIT, sort=True):
        genotypes = block[GROUP].unique()
        if len(genotypes) != 1:
            raise ValueError(
                "donor %s carries more than one genotype; genotype must vary "
                "between donors, never within a donor" % donor
            )
        level = genotypes[0]
        donor_blocks[level].append(block[OUTCOME].to_numpy(dtype=float))
        donor_labels[level].append(donor)

    n_ref = len(donor_blocks[REFERENCE_LEVEL])
    n_cmp = len(donor_blocks[COMPARISON_LEVEL])

    # Observed difference in group means.
    obs_ref = np.concatenate(donor_blocks[REFERENCE_LEVEL]).mean()
    obs_cmp = np.concatenate(donor_blocks[COMPARISON_LEVEL]).mean()
    observed_diff = obs_cmp - obs_ref

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_resamples, dtype=float)

    ref_blocks = donor_blocks[REFERENCE_LEVEL]
    cmp_blocks = donor_blocks[COMPARISON_LEVEL]

    for i in range(n_resamples):
        # Draw donors (not wells) with replacement, within each group.
        ref_draw = rng.integers(0, n_ref, size=n_ref)
        cmp_draw = rng.integers(0, n_cmp, size=n_cmp)

        # A drawn donor contributes all of its wells, every time it is drawn.
        ref_wells = np.concatenate([ref_blocks[j] for j in ref_draw])
        cmp_wells = np.concatenate([cmp_blocks[j] for j in cmp_draw])

        diffs[i] = cmp_wells.mean() - ref_wells.mean()

    alpha = 1.0 - ci_level
    lower = float(np.percentile(diffs, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(diffs, 100.0 * (1.0 - alpha / 2.0)))

    return {
        "observed_diff": float(observed_diff),
        "mean_reference": float(obs_ref),
        "mean_comparison": float(obs_cmp),
        "ci_low": lower,
        "ci_high": upper,
        "ci_level": ci_level,
        "n_resamples": n_resamples,
        "seed": seed,
        "n_donors_reference": n_ref,
        "n_donors_comparison": n_cmp,
        "n_donors_total": n_ref + n_cmp,
        "donor_labels": donor_labels,
        "boot_diffs": diffs,
    }


# ---------------------------------------------------------------------------
# Descriptives
# ---------------------------------------------------------------------------
def describe(wells):
    donor_means = (
        wells.groupby([UNIT, GROUP], sort=True)[OUTCOME].mean().reset_index()
    )
    within = wells.groupby(UNIT, sort=True)[OUTCOME].std(ddof=1)
    within = within.to_frame("within_sd").join(
        wells.groupby(UNIT, sort=True)[GROUP].first()
    )

    lines = []
    for level in (REFERENCE_LEVEL, COMPARISON_LEVEL):
        sub_wells = wells.loc[wells[GROUP] == level, OUTCOME]
        sub_donors = donor_means.loc[donor_means[GROUP] == level, OUTCOME]
        sub_within = within.loc[within[GROUP] == level, "within_sd"]
        lines.append(
            {
                "genotype": level,
                "n_donors": int(sub_donors.shape[0]),
                "n_wells": int(sub_wells.shape[0]),
                "well_mean": float(sub_wells.mean()),
                "donor_mean_of_means": float(sub_donors.mean()),
                "between_donor_sd": float(sub_donors.std(ddof=1)),
                "mean_within_donor_sd": float(sub_within.mean()),
                "donor_mean_min": float(sub_donors.min()),
                "donor_mean_max": float(sub_donors.max()),
            }
        )
    return pd.DataFrame(lines), donor_means


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def main():
    wells = load_wells()

    n_rows = wells.shape[0]
    wells_per_donor = wells.groupby(UNIT)[OUTCOME].size()

    print("=" * 78)
    print("ORGANOID BARRIER FUNCTION BY TIGHT-JUNCTION GENOTYPE")
    print("=" * 78)
    print()
    print("Data: %s" % CSV_NAME)
    print("Rows (wells): %d" % n_rows)
    print("Donors: %d" % wells[UNIT].nunique())
    print(
        "Wells per donor: min %d, max %d"
        % (int(wells_per_donor.min()), int(wells_per_donor.max()))
    )
    print(
        "Genotype varies between donors, never between wells within a donor;"
        "\neach donor's %d wells are technical replicates of that one donor."
        % int(wells_per_donor.max())
    )
    print()

    desc, donor_means = describe(wells)
    print("-" * 78)
    print("DESCRIPTIVES")
    print("-" * 78)
    for _, row in desc.iterrows():
        print(
            "%-12s donors=%d wells=%d | well mean=%7.1f | donor-mean of donor "
            "means=%7.1f" % (
                row["genotype"],
                row["n_donors"],
                row["n_wells"],
                row["well_mean"],
                row["donor_mean_of_means"],
            )
        )
        print(
            "%-12s between-donor SD=%5.1f | mean within-donor SD=%5.1f | donor "
            "means %6.1f to %6.1f" % (
                "",
                row["between_donor_sd"],
                row["mean_within_donor_sd"],
                row["donor_mean_min"],
                row["donor_mean_max"],
            )
        )
    print()
    print(
        "Between-donor spread exceeds within-donor spread, so wells from the "
        "same\ndonor are correlated and cannot be treated as independent."
    )
    print()

    # -----------------------------------------------------------------
    # PRIMARY
    # -----------------------------------------------------------------
    boot = cluster_bootstrap(wells, N_RESAMPLES, SEED, CI_LEVEL)

    print("=" * 78)
    print("PRIMARY AND VALID ANALYSIS")
    print("Donor-level cluster bootstrap (the donor is the independent "
          "replicate)")
    print("=" * 78)
    print(
        "Resampling unit ......... donor (%s); all %d wells of a drawn donor "
        "move together" % (UNIT, int(wells_per_donor.max()))
    )
    print(
        "Sample size ............. %d donors per group, %d donors in total"
        % (boot["n_donors_reference"], boot["n_donors_total"])
    )
    print("Resamples ............... %d" % boot["n_resamples"])
    print("Random seed ............. %d" % boot["seed"])
    print()
    print(
        "Mean TEER, %-12s %8.1f ohm-cm2" % (
            REFERENCE_LEVEL + ":", boot["mean_reference"])
    )
    print(
        "Mean TEER, %-12s %8.1f ohm-cm2" % (
            COMPARISON_LEVEL + ":", boot["mean_comparison"])
    )
    print(
        "Observed difference (%s minus %s): %+.1f ohm-cm2"
        % (COMPARISON_LEVEL, REFERENCE_LEVEL, boot["observed_diff"])
    )
    print(
        "%.0f%% percentile bootstrap CI: [%+.1f, %+.1f] ohm-cm2"
        % (100 * boot["ci_level"], boot["ci_low"], boot["ci_high"])
    )
    excludes_zero = not (boot["ci_low"] <= 0.0 <= boot["ci_high"])
    print(
        "Interval excludes zero: %s" % ("yes" if excludes_zero else "no")
    )
    print()
    print(
        "This donor-level resampling result is the inferential result of the\n"
        "project. Every conclusion is based on it."
    )
    print()

    # -----------------------------------------------------------------
    # ILLUSTRATIVE CONTRAST
    # -----------------------------------------------------------------
    ref_wells = wells.loc[wells[GROUP] == REFERENCE_LEVEL, OUTCOME].to_numpy()
    cmp_wells = wells.loc[wells[GROUP] == COMPARISON_LEVEL, OUTCOME].to_numpy()
    t_stat, p_value = stats.ttest_ind(cmp_wells, ref_wells, equal_var=True)

    print("=" * 78)
    print("ILLUSTRATIVE CONTRAST ONLY -- INVALID FOR INFERENCE")
    print("Well-level two-sample t-test on all %d wells" % n_rows)
    print("=" * 78)
    print(
        "Assumed sample size ..... %d wells per group, %d wells in total"
        % (len(ref_wells), n_rows)
    )
    print("t statistic ............. %.3f" % float(t_stat))
    print("p-value ................. %.3e" % float(p_value))
    print()
    print(
        "THIS P-VALUE IS INVALID FOR INFERENCE HERE. It counts the technical\n"
        "replicates of %d donors as %d independent subjects. Genotype varies\n"
        "between donors and not between wells, so the wells inside a donor\n"
        "carry no extra independent information about genotype. The number is\n"
        "printed only to show how far the apparent evidence inflates when\n"
        "technical replicates are counted as subjects. It is not used for any\n"
        "conclusion in this project." % (boot["n_donors_total"], n_rows)
    )
    print()
    print("=" * 78)
    print(
        "SUMMARY: primary = donor-level cluster bootstrap (valid, n=%d donors);"
        % boot["n_donors_total"]
    )
    print(
        "         secondary = well-level t-test (invalid for inference, shown "
        "for illustration only)."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
