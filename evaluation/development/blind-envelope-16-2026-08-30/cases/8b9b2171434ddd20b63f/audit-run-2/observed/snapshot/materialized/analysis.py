"""Hare condition analysis: two-landscape comparison over a pre-declared family
of five outcomes, with family-wise error control by label shuffling.

The multiplicity correction is written out by hand below (max-statistic
permutation); no ready-made multiple-comparison routine is used.

Pre-declared design decisions, fixed before the data were analysed:
  * outcome family, in order: body_mass_kg, hind_foot_mm, cortisol_ng_g,
    haemoglobin_g_dl, egg_count_epg
  * two-group test statistic: Welch two-sample t statistic
  * number of label shuffles: 4000
  * family-wise significance level: 0.05
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- settings --

DATA_FILE = "hares.csv"
GROUP_COL = "landscape"
GROUP_A = "mixed_farmland"
GROUP_B = "intensive_arable"

# The pre-declared outcome family, in the pre-declared order.
OUTCOMES = [
    "body_mass_kg",
    "hind_foot_mm",
    "cortisol_ng_g",
    "haemoglobin_g_dl",
    "egg_count_epg",
]

# Pre-declared number of label shuffles. Stated openly, fixed in advance.
N_SHUFFLES = 4000

# Pre-declared family-wise error rate.
ALPHA = 0.05

# Fixed seed so the shuffling run repeats exactly.
SEED = 20260830


# --------------------------------------------------------------- statistic --

def welch_t(values, in_group_a):
    """Welch two-sample t statistic for each column of `values`.

    `values` is (n_rows, n_outcomes); `in_group_a` is a boolean mask of length
    n_rows that is True for group A rows. Returns one t statistic per column,
    signed as group A minus group B.
    """
    a = values[in_group_a, :]
    b = values[~in_group_a, :]

    n_a = a.shape[0]
    n_b = b.shape[0]

    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)

    # ddof=1: sample variance.
    var_a = a.var(axis=0, ddof=1)
    var_b = b.var(axis=0, ddof=1)

    standard_error = np.sqrt(var_a / n_a + var_b / n_b)
    return (mean_a - mean_b) / standard_error


# ------------------------------------------------------------------- main ---

def main():
    data = pd.read_csv(DATA_FILE)

    groups = data[GROUP_COL].to_numpy()
    in_group_a = groups == GROUP_A

    values = data[OUTCOMES].to_numpy(dtype=float)

    n_rows = values.shape[0]
    n_a = int(in_group_a.sum())
    n_b = int((~in_group_a).sum())

    # Observed group means and observed statistics.
    mean_a = values[in_group_a, :].mean(axis=0)
    mean_b = values[~in_group_a, :].mean(axis=0)
    observed_t = welch_t(values, in_group_a)

    # --- family-wise control by label shuffling -------------------------------
    #
    # On each of the 4000 shuffles the landscape labels are permuted across all
    # 64 hares at once, so every outcome is re-tested under the same permuted
    # labels and the correlation between outcomes is preserved. From each
    # shuffle we keep ONLY the single largest absolute statistic seen anywhere
    # in the five-outcome family. The 4000 kept values form one family-maximum
    # reference distribution. Comparing each observed statistic against that
    # single reference is what holds the family-wise error rate at ALPHA across
    # all five outcomes at once.
    rng = np.random.default_rng(SEED)
    family_maxima = np.empty(N_SHUFFLES, dtype=float)

    for i in range(N_SHUFFLES):
        shuffled = rng.permutation(in_group_a)
        shuffled_t = welch_t(values, shuffled)
        family_maxima[i] = np.max(np.abs(shuffled_t))

    # Family-wise adjusted significance for each outcome: the share of the
    # family-maximum reference distribution at or beyond that outcome's own
    # observed absolute statistic. The observed labelling is counted as one
    # additional draw (the usual +1 convention), so the value is never zero.
    fwer_p = np.empty(len(OUTCOMES), dtype=float)
    for j in range(len(OUTCOMES)):
        at_or_beyond = int(np.sum(family_maxima >= abs(observed_t[j])))
        fwer_p[j] = (1.0 + at_or_beyond) / (1.0 + N_SHUFFLES)

    # ----------------------------------------------------------- reporting ---

    print("Hare condition analysis")
    print("=" * 72)
    print("Rows: {0}   {1}: n = {2}   {3}: n = {4}".format(
        n_rows, GROUP_A, n_a, GROUP_B, n_b))
    print("Outcome family (pre-declared order): {0}".format(", ".join(OUTCOMES)))
    print("Statistic: Welch two-sample t ({0} minus {1})".format(GROUP_A, GROUP_B))
    print("Label shuffles: {0}   seed: {1}   family-wise alpha: {2}".format(
        N_SHUFFLES, SEED, ALPHA))
    print("Family-maximum reference distribution: {0} values, "
          "max = {1:.4f}, 95th pct = {2:.4f}".format(
              N_SHUFFLES,
              float(family_maxima.max()),
              float(np.percentile(family_maxima, 95))))
    print()

    header = "{0:<18} {1:>14} {2:>16} {3:>10} {4:>12}  {5}".format(
        "outcome", "mean_mixed", "mean_intensive", "welch_t", "fwer_p", "verdict")
    print(header)
    print("-" * len(header))

    for j, name in enumerate(OUTCOMES):
        verdict = ("significant at FWER 0.05" if fwer_p[j] < ALPHA
                   else "not significant at FWER 0.05")
        print("{0:<18} {1:>14.4f} {2:>16.4f} {3:>10.4f} {4:>12.5f}  {5}".format(
            name, mean_a[j], mean_b[j], observed_t[j], fwer_p[j], verdict))

    print()
    print("Verdicts come only from the family-maximum shuffling reference. "
          "No unshuffled per-outcome p-value is computed or used.")


if __name__ == "__main__":
    main()
