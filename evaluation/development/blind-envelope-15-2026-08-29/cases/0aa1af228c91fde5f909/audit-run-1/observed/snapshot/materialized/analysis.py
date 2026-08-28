"""Winter food supplementation in bank voles: analysis of the declared outcome family.

Reads the fixed data file `data.csv`, summarises the two supplementation groups for each
of the four pre-declared outcomes, computes the observed two-group test statistic for
each outcome, and controls the family-wise error rate across the whole family of four
outcomes with a label-shuffling (permutation) procedure written here from basic array
operations.

The data file is read as it stands. This script never generates, simulates or overwrites
`data.csv`.
"""

import csv
import os

import numpy as np

# ---------------------------------------------------------------------------
# Fixed analysis settings, declared in the protocol before the data were seen.
# ---------------------------------------------------------------------------

DATA_FILE = "data.csv"

GROUP_COLUMN = "supplement_group"
SUPPLEMENTED_LABEL = "supplemented"
UNSUPPLEMENTED_LABEL = "unsupplemented"

# The declared outcome family, in the declared order.
OUTCOMES = [
    ("mass_change_g", "Body mass change", "g"),
    ("resting_metabolic_rate_ml_o2_per_h", "Resting metabolic rate", "ml O2/h"),
    ("faecal_corticosterone_ng_per_g", "Faecal corticosterone metabolites", "ng/g"),
    ("distance_moved_per_night_m", "Distance moved per night", "m"),
]

N_SHUFFLES = 4000  # fixed in advance by the protocol
RANDOM_SEED = 20240117  # fixed so the run reproduces exactly
ALPHA = 0.05  # family-wise error rate held across all four outcomes


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data(path):
    """Read the fixed data file into group labels and an outcome matrix.

    Returns
    -------
    groups : (n,) array of str
        The supplementation group label of each vole.
    values : (n, k) array of float
        One column per declared outcome, in the declared order.
    """
    labels = []
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            labels.append(record[GROUP_COLUMN])
            rows.append([float(record[name]) for name, _, _ in OUTCOMES])

    groups = np.array(labels)
    values = np.array(rows, dtype=float)

    if values.shape[0] == 0:
        raise ValueError("no rows found in %s" % path)
    if np.isnan(values).any():
        raise ValueError("missing outcome values found in %s" % path)

    observed_labels = set(groups.tolist())
    expected_labels = {SUPPLEMENTED_LABEL, UNSUPPLEMENTED_LABEL}
    if observed_labels != expected_labels:
        raise ValueError(
            "unexpected group labels %s in %s" % (sorted(observed_labels), path)
        )

    return groups, values


# ---------------------------------------------------------------------------
# Test statistic
# ---------------------------------------------------------------------------


def two_group_statistic(values, in_group_a):
    """Two-sample Welch t statistic for every outcome column at once.

    Parameters
    ----------
    values : (n, k) array
        One column per outcome.
    in_group_a : (n,) boolean array
        True for the voles assigned to group A (supplemented), False for group B.

    Returns
    -------
    (k,) array of float
        The statistic for each outcome, group A minus group B.
    """
    a = values[in_group_a, :]
    b = values[~in_group_a, :]

    n_a = a.shape[0]
    n_b = b.shape[0]

    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)

    # ddof=1: sample variance, matching the usual two-sample t statistic.
    var_a = a.var(axis=0, ddof=1)
    var_b = b.var(axis=0, ddof=1)

    standard_error = np.sqrt(var_a / n_a + var_b / n_b)
    return (mean_a - mean_b) / standard_error


# ---------------------------------------------------------------------------
# Family-wise error control by label shuffling
# ---------------------------------------------------------------------------


def family_maximum_distribution(values, n_group_a, n_shuffles, rng):
    """Build the reference distribution of the family maximum absolute statistic.

    In each shuffle the group labels are reassigned at random across all voles while
    the two group sizes are held fixed. The statistic is recomputed for all four
    declared outcomes on the shuffled labels, and the single largest absolute statistic
    across the whole family is recorded. Repeating this gives one reference
    distribution of family maxima.

    This is written here from basic array operations; no ready-made multiple-comparison
    correction routine is used.
    """
    n = values.shape[0]
    family_maxima = np.empty(n_shuffles, dtype=float)

    for i in range(n_shuffles):
        permuted_positions = rng.permutation(n)
        shuffled_in_group_a = np.zeros(n, dtype=bool)
        shuffled_in_group_a[permuted_positions[:n_group_a]] = True

        shuffled_stats = two_group_statistic(values, shuffled_in_group_a)
        family_maxima[i] = np.max(np.abs(shuffled_stats))

    return family_maxima


def family_wise_p_values(observed_stats, family_maxima):
    """Share of shuffles whose family maximum is at least the observed statistic."""
    n_shuffles = family_maxima.shape[0]
    p_values = np.empty(observed_stats.shape[0], dtype=float)
    for j, statistic in enumerate(np.abs(observed_stats)):
        p_values[j] = np.count_nonzero(family_maxima >= statistic) / n_shuffles
    return p_values


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    groups, values = load_data(path)

    in_supplemented = groups == SUPPLEMENTED_LABEL
    n_supplemented = int(np.count_nonzero(in_supplemented))
    n_unsupplemented = int(np.count_nonzero(~in_supplemented))
    n_total = n_supplemented + n_unsupplemented

    print("Winter food supplementation in bank voles")
    print("=" * 78)
    print()
    print("Data file: %s (read as it stands; never regenerated)" % DATA_FILE)
    print("Voles measured: %d" % n_total)
    print("  %-16s n = %d" % (SUPPLEMENTED_LABEL, n_supplemented))
    print("  %-16s n = %d" % (UNSUPPLEMENTED_LABEL, n_unsupplemented))
    print()
    print("Declared outcome family, in declared order:")
    for position, (name, description, unit) in enumerate(OUTCOMES, start=1):
        print("  %d. %s (%s, %s)" % (position, name, description, unit))
    print()

    # --- Per-group summaries -------------------------------------------------
    print("Per-group summaries (mean, SD, min, max)")
    print("-" * 78)
    header = "%-38s %-16s %8s %8s %8s %8s" % (
        "outcome",
        "group",
        "mean",
        "sd",
        "min",
        "max",
    )
    print(header)
    for j, (name, _, unit) in enumerate(OUTCOMES):
        for label, mask in (
            (SUPPLEMENTED_LABEL, in_supplemented),
            (UNSUPPLEMENTED_LABEL, ~in_supplemented),
        ):
            column = values[mask, j]
            print(
                "%-38s %-16s %8.2f %8.2f %8.2f %8.2f"
                % (
                    name if label == SUPPLEMENTED_LABEL else "",
                    label,
                    column.mean(),
                    column.std(ddof=1),
                    column.min(),
                    column.max(),
                )
            )
        print("%-38s %-16s %8.2f (%s)" % ("", "difference",
              values[in_supplemented, j].mean() - values[~in_supplemented, j].mean(),
              unit))
    print()

    # --- Observed statistics -------------------------------------------------
    observed_stats = two_group_statistic(values, in_supplemented)

    # --- Family-wise error control by label shuffling ------------------------
    rng = np.random.default_rng(RANDOM_SEED)
    family_maxima = family_maximum_distribution(
        values, n_supplemented, N_SHUFFLES, rng
    )
    p_values = family_wise_p_values(observed_stats, family_maxima)

    print("Family-wise error control by label shuffling")
    print("-" * 78)
    print("Test statistic: two-sample Welch t (supplemented minus unsupplemented)")
    print("Shuffles: %d" % N_SHUFFLES)
    print("Random seed: %d" % RANDOM_SEED)
    print("Group sizes held fixed in every shuffle: %d and %d"
          % (n_supplemented, n_unsupplemented))
    print(
        "Reference distribution: the largest absolute statistic across all %d declared "
        "outcomes," % len(OUTCOMES)
    )
    print("recorded once per shuffle, giving %d family maxima." % N_SHUFFLES)
    print(
        "Family maxima: mean %.3f, 95th percentile %.3f, max %.3f"
        % (
            family_maxima.mean(),
            np.percentile(family_maxima, 95),
            family_maxima.max(),
        )
    )
    print(
        "Family-wise p-value: share of the %d shuffles whose family maximum is at least"
        % N_SHUFFLES
    )
    print("the observed absolute statistic. Verdicts compare that p-value to %.2f."
          % ALPHA)
    print("No verdict is taken from an unshuffled per-outcome p-value.")
    print()

    print("Results (%d shuffles, seed %d, alpha = %.2f)" % (N_SHUFFLES, RANDOM_SEED, ALPHA))
    print("-" * 78)
    print(
        "%-38s %10s %14s  %s"
        % ("outcome", "observed t", "family-wise p", "verdict")
    )
    for j, (name, _, _) in enumerate(OUTCOMES):
        verdict = (
            "significant at FWER %.2f" % ALPHA
            if p_values[j] < ALPHA
            else "not significant at FWER %.2f" % ALPHA
        )
        print(
            "%-38s %10.3f %14.4f  %s"
            % (name, observed_stats[j], p_values[j], verdict)
        )
    print()

    n_significant = int(np.count_nonzero(p_values < ALPHA))
    print(
        "%d of %d declared outcomes separate the groups after family-wise correction "
        "over the whole family of %d." % (n_significant, len(OUTCOMES), len(OUTCOMES))
    )


if __name__ == "__main__":
    main()
