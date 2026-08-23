"""Twelve-week probing-depth comparison of two toothpaste formulations.

Reads probing_depth.csv, runs the primary patient-clustered analysis, and prints
the results.  Teeth from one mouth are not independent, so the primary inference
treats the PATIENT as the resampling unit.

Primary route (stated explicitly in the printed output): a self-written
cluster bootstrap that resamples WHOLE PATIENTS with replacement, stratified by
paste arm, and rebuilds the between-arm difference in probing depth on every
replicate.  No clustered-inference library routine is used for the primary
result; the resampling loop below is the whole method.

A naive tooth-level two-sample t-test on all 208 teeth is also printed, purely
as an illustrative contrast.  It is NOT a valid basis for inference.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats

# Resolve the data file next to this script so the analysis runs from anywhere.
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probing_depth.csv")
OUTCOME = "probing_depth_mm"
ARM = "paste_arm"
CLUSTER = "patient_code"
TREAT_ARM = "stannous_fluoride"
CONTROL_ARM = "sodium_fluoride"

N_BOOT = 20000
SEED = 20260822
CI_LEVEL = 0.95


def load_data(path=DATA_FILE):
    df = pd.read_csv(path)
    expected = [
        "patient_code",
        "paste_arm",
        "tooth_site",
        "bleeding_on_probing",
        "probing_depth_mm",
    ]
    if list(df.columns) != expected:
        raise ValueError("unexpected columns: %r" % (list(df.columns),))
    if df.isna().any().any():
        raise ValueError("data file contains missing values")
    return df


def patient_table(df):
    """One row per patient: arm, number of teeth, mean depth."""
    tab = (
        df.groupby([CLUSTER, ARM], as_index=False)
        .agg(n_teeth=(OUTCOME, "size"), mean_depth=(OUTCOME, "mean"))
        .sort_values(CLUSTER)
        .reset_index(drop=True)
    )
    return tab


def arm_difference(patients):
    """Stannous minus sodium, as a difference of arm means of patient means."""
    a = patients.loc[patients[ARM] == TREAT_ARM, "mean_depth"].to_numpy()
    b = patients.loc[patients[ARM] == CONTROL_ARM, "mean_depth"].to_numpy()
    return a.mean() - b.mean()


def cluster_bootstrap(patients, n_boot=N_BOOT, seed=SEED):
    """Resample whole patients with replacement, within arm, n_boot times.

    Each replicate draws 13 stannous patients and 13 sodium patients with
    replacement from the observed patients of that arm, carrying each drawn
    patient's whole mouth (all eight of its teeth) along with it, then rebuilds
    the arm difference.  Sampling the patient rather than the tooth is what
    keeps the within-mouth correlation in the uncertainty estimate.
    """
    rng = np.random.default_rng(seed)
    treat = patients.loc[patients[ARM] == TREAT_ARM, "mean_depth"].to_numpy()
    control = patients.loc[patients[ARM] == CONTROL_ARM, "mean_depth"].to_numpy()
    n_t, n_c = treat.size, control.size

    reps = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        t_idx = rng.integers(0, n_t, size=n_t)
        c_idx = rng.integers(0, n_c, size=n_c)
        reps[i] = treat[t_idx].mean() - control[c_idx].mean()
    return reps


def bootstrap_p_value(reps, observed):
    """Two-sided bootstrap p-value by recentring the replicates on the null.

    Shift the bootstrap distribution so that it is centred on a zero difference,
    then ask how often a shifted replicate is at least as extreme in absolute
    value as the difference actually observed.
    """
    shifted = reps - observed
    extreme = int(np.sum(np.abs(shifted) >= abs(observed)))
    return (extreme + 1) / (reps.size + 1)


def main():
    df = load_data()
    patients = patient_table(df)

    n_patients = patients.shape[0]
    n_teeth = df.shape[0]
    teeth_per_patient = sorted(patients["n_teeth"].unique())

    print("=" * 78)
    print("PROBING DEPTH AT TWELVE WEEKS: STANNOUS vs SODIUM FLUORIDE PASTE")
    print("=" * 78)
    print()
    print("Data")
    print("----")
    print("File                     : %s" % os.path.basename(DATA_FILE))
    print("Rows (index teeth)       : %d" % n_teeth)
    print("Patients (randomised)    : %d" % n_patients)
    print("Teeth per patient        : %s" % ", ".join(str(v) for v in teeth_per_patient))
    print("One row is one index tooth in one patient; a patient appears on eight rows.")
    print()

    for arm in (TREAT_ARM, CONTROL_ARM):
        sub_p = patients[patients[ARM] == arm]
        sub_t = df[df[ARM] == arm]
        bleed = (sub_t["bleeding_on_probing"] == "yes").sum()
        print(
            "%-18s patients=%2d teeth=%3d  tooth-level mean depth=%.3f mm (SD %.3f)"
            % (arm, sub_p.shape[0], sub_t.shape[0], sub_t[OUTCOME].mean(), sub_t[OUTCOME].std(ddof=1))
        )
        print(
            "%-18s patient-mean depth=%.3f mm (SD between patients %.3f)  bleeding teeth=%d/%d (%.1f%%)"
            % ("", sub_p["mean_depth"].mean(), sub_p["mean_depth"].std(ddof=1), bleed, sub_t.shape[0], 100.0 * bleed / sub_t.shape[0])
        )
    print()

    # ------------------------------------------------------------------
    # PRIMARY ANALYSIS
    # ------------------------------------------------------------------
    observed = arm_difference(patients)
    reps = cluster_bootstrap(patients)
    alpha = 1.0 - CI_LEVEL
    lo, hi = np.percentile(reps, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    se = reps.std(ddof=1)
    p_boot = bootstrap_p_value(reps, observed)

    print("PRIMARY ANALYSIS (valid): self-written cluster bootstrap")
    print("-" * 78)
    print("Route taken: a resampling procedure written by hand in this script, not a")
    print("library clustered-inference routine.  Each of the %d replicates draws whole" % N_BOOT)
    print("PATIENTS with replacement (13 per arm, stratified by arm), carries all eight")
    print("teeth of every drawn patient, and rebuilds the between-arm difference.")
    print("The patient is therefore the independent unit, as the randomisation was.")
    print("Random seed: %d (results are reproducible)." % SEED)
    print()
    print("Effect measure : mean probing depth, stannous fluoride minus sodium fluoride")
    print("Point estimate : %+.3f mm" % observed)
    print("Bootstrap SE   : %.3f mm" % se)
    print("%.0f%% percentile CI: %+.3f mm to %+.3f mm" % (100 * CI_LEVEL, lo, hi))
    print("Bootstrap p    : %.4f (two-sided, replicates recentred on the null)" % p_boot)
    print()

    # ------------------------------------------------------------------
    # ILLUSTRATIVE CONTRAST -- NOT VALID FOR INFERENCE
    # ------------------------------------------------------------------
    t_depth = df.loc[df[ARM] == TREAT_ARM, OUTCOME].to_numpy()
    c_depth = df.loc[df[ARM] == CONTROL_ARM, OUTCOME].to_numpy()
    t_stat, p_naive = stats.ttest_ind(t_depth, c_depth, equal_var=False)
    naive_diff = t_depth.mean() - c_depth.mean()
    n1, n2 = t_depth.size, c_depth.size
    naive_se = np.sqrt(t_depth.var(ddof=1) / n1 + c_depth.var(ddof=1) / n2)
    dfree = (t_depth.var(ddof=1) / n1 + c_depth.var(ddof=1) / n2) ** 2 / (
        (t_depth.var(ddof=1) / n1) ** 2 / (n1 - 1) + (c_depth.var(ddof=1) / n2) ** 2 / (n2 - 1)
    )
    tcrit = stats.t.ppf(0.975, dfree)
    naive_lo, naive_hi = naive_diff - tcrit * naive_se, naive_diff + tcrit * naive_se

    print("ILLUSTRATIVE CONTRAST ONLY -- NOT A VALID BASIS FOR INFERENCE")
    print("-" * 78)
    print("Naive tooth-level two-sample Welch t-test on all %d teeth:" % n_teeth)
    print("Point estimate : %+.3f mm" % naive_diff)
    print("Naive SE       : %.3f mm" % naive_se)
    print("Naive 95%% CI   : %+.3f mm to %+.3f mm" % (naive_lo, naive_hi))
    print("t = %.3f, df = %.1f, p = %.3g" % (t_stat, dfree, p_naive))
    print()
    print("WARNING: this tooth-level test is NOT a valid basis for inference.  It treats")
    print("the eight teeth from the same patient as %d independent observations when they" % n_teeth)
    print("are not: they share one mouth, one plaque-control habit and one smoking status,")
    print("so they move up and down together.  Counting them as independent inflates the")
    print("sample size from %d randomised patients to %d teeth, shrinks the standard error" % (n_patients, n_teeth))
    print("and the p-value, and makes the result look far more certain than it is.  It is")
    print("shown here only as a contrast with the valid patient-clustered result above.")
    print()

    print("The honest patient-clustered SE is %.2f times the naive tooth-level SE." % (se / naive_se))
    print("=" * 78)


if __name__ == "__main__":
    main()
