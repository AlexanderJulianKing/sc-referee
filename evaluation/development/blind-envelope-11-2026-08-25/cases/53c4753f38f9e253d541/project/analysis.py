"""Quinoa deficit-irrigation experiment: analysis of the five declared outcomes.

Reads harvest_records.csv (one row per potted plant), summarises each declared
outcome by irrigation regime, and tests all five outcomes against a family-wise
error rate of 0.05 using a max-statistic label-shuffling (permutation) procedure
written out explicitly here rather than taken from a library correction routine.

Run from the project root:
    python analysis.py
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Fixed analysis constants, decided before the data were looked at.
# ---------------------------------------------------------------------------

CSV_PATH = "harvest_records.csv"

GROUP_COLUMN = "irrigation_regime"
GROUP_A = "full"       # full irrigation
GROUP_B = "deficit"    # deficit irrigation

# The five outcomes in the order they were declared in the experimental plan.
DECLARED_OUTCOMES = [
    "seed_yield_g",
    "thousand_seed_weight_g",
    "plant_height_cm",
    "seed_saponin_mg_g",
    "midday_leaf_water_potential_mpa",
]

# Exact number of label shuffles, fixed in advance: five thousand.
N_SHUFFLES = 5000

# Seed fixed so the shuffling reproduces exactly.
RANDOM_SEED = 20260825

# Family-wise significance level applied across all five declared outcomes.
FAMILY_ALPHA = 0.05


# ---------------------------------------------------------------------------
# Test statistic
# ---------------------------------------------------------------------------

def welch_t(values, is_group_a):
    """Welch two-sample t statistic for one outcome, group A minus group B.

    `values` is a 1-D array of the outcome for all plants.
    `is_group_a` is a boolean array of the same length, True for full irrigation.
    A positive statistic means full irrigation is higher than deficit.
    """
    a = values[is_group_a]
    b = values[~is_group_a]
    n_a = a.size
    n_b = b.size
    var_a = a.var(ddof=1)
    var_b = b.var(ddof=1)
    se = np.sqrt(var_a / n_a + var_b / n_b)
    return (a.mean() - b.mean()) / se


def welch_t_all_outcomes(matrix, is_group_a):
    """Welch t statistic for every outcome at once.

    `matrix` has one column per declared outcome, one row per plant.
    Returns a 1-D array of statistics, one per column, in column order.
    """
    a = matrix[is_group_a, :]
    b = matrix[~is_group_a, :]
    n_a = a.shape[0]
    n_b = b.shape[0]
    var_a = a.var(axis=0, ddof=1)
    var_b = b.var(axis=0, ddof=1)
    se = np.sqrt(var_a / n_a + var_b / n_b)
    return (a.mean(axis=0) - b.mean(axis=0)) / se


# ---------------------------------------------------------------------------
# Load and check the data
# ---------------------------------------------------------------------------

def load_data(path):
    frame = pd.read_csv(path)

    missing_columns = [
        c for c in [GROUP_COLUMN] + DECLARED_OUTCOMES if c not in frame.columns
    ]
    if missing_columns:
        raise ValueError(f"CSV is missing expected columns: {missing_columns}")

    observed_groups = sorted(frame[GROUP_COLUMN].unique())
    if observed_groups != sorted([GROUP_A, GROUP_B]):
        raise ValueError(
            f"Expected exactly the groups {sorted([GROUP_A, GROUP_B])}, "
            f"found {observed_groups}"
        )

    n_missing = int(frame[DECLARED_OUTCOMES].isna().sum().sum())
    if n_missing:
        raise ValueError(f"Found {n_missing} missing outcome cells; expected none.")

    return frame


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def print_group_counts(frame):
    counts = frame[GROUP_COLUMN].value_counts()
    print("Plants per irrigation regime")
    print("-" * 60)
    for group in (GROUP_A, GROUP_B):
        print(f"  {group:<8s} {int(counts[group]):d} plants")
    print(f"  {'total':<8s} {len(frame):d} plants")
    print()


def print_group_summaries(frame):
    print("Per-group summary of each declared outcome (mean, SD)")
    print("-" * 78)
    header = f"{'outcome':<34s} {'group':<8s} {'n':>3s} {'mean':>9s} {'SD':>8s}"
    print(header)
    for outcome in DECLARED_OUTCOMES:
        for group in (GROUP_A, GROUP_B):
            values = frame.loc[frame[GROUP_COLUMN] == group, outcome].to_numpy()
            print(
                f"{outcome:<34s} {group:<8s} {values.size:>3d} "
                f"{values.mean():>9.3f} {values.std(ddof=1):>8.3f}"
            )
    print()


# ---------------------------------------------------------------------------
# Family-wise max-statistic permutation procedure
# ---------------------------------------------------------------------------

def family_max_reference(matrix, is_group_a, n_shuffles, seed):
    """Build the family-maximum reference distribution.

    On each of `n_shuffles` shuffles, one single permutation of the irrigation
    labels is applied to all plants and reused for every outcome, so the
    correlation between the five outcomes is preserved. The Welch t statistic
    is recomputed for all five outcomes on those shuffled labels and only the
    largest absolute value among the five is retained.

    Returns an array of length `n_shuffles` holding those family maxima.
    """
    rng = np.random.default_rng(seed)
    labels = is_group_a.copy()
    maxima = np.empty(n_shuffles, dtype=float)
    for i in range(n_shuffles):
        shuffled = rng.permutation(labels)
        stats = welch_t_all_outcomes(matrix, shuffled)
        maxima[i] = np.max(np.abs(stats))
    return maxima


def family_p_value(observed_statistic, maxima):
    """Standing of one observed statistic in the family-maximum distribution.

    Uses the conservative add-one estimator, which counts the observed
    configuration itself as one of the possible label assignments and so never
    reports a p-value of exactly zero.
    """
    n_at_least = int(np.sum(maxima >= abs(observed_statistic)))
    return (n_at_least + 1) / (maxima.size + 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    frame = load_data(CSV_PATH)

    print("=" * 78)
    print("Quinoa deficit-irrigation experiment: analysis of five declared outcomes")
    print("=" * 78)
    print()

    print_group_counts(frame)
    print_group_summaries(frame)

    matrix = frame[DECLARED_OUTCOMES].to_numpy(dtype=float)
    is_group_a = (frame[GROUP_COLUMN] == GROUP_A).to_numpy()

    observed = welch_t_all_outcomes(matrix, is_group_a)

    maxima = family_max_reference(matrix, is_group_a, N_SHUFFLES, RANDOM_SEED)

    # The family-wise critical value: the (1 - alpha) quantile of the family
    # maxima. Any observed statistic beyond it is significant at the family level.
    critical_value = float(np.quantile(maxima, 1.0 - FAMILY_ALPHA))

    print("Family-wise error control by label shuffling")
    print("-" * 78)
    print(f"  Number of label shuffles: {N_SHUFFLES:d} (exactly five thousand)")
    print(f"  Random seed:              {RANDOM_SEED:d}")
    print(f"  Test statistic:           Welch two-sample t, full minus deficit")
    print(f"  Family level:             {FAMILY_ALPHA:.2f}")
    print(f"  Outcomes in the family:   {len(DECLARED_OUTCOMES):d}")
    print(
        f"  Family-maximum reference: min {maxima.min():.3f}, "
        f"median {np.median(maxima):.3f}, max {maxima.max():.3f}"
    )
    print(
        f"  Critical value (95th percentile of the family maxima): "
        f"{critical_value:.3f}"
    )
    print()

    print("Result for each declared outcome, in the declared order")
    print("-" * 78)
    print(
        f"{'#':<3s}{'outcome':<34s}{'obs |t|':>9s}{'family p':>10s}"
        f"{'  ':2s}{'verdict':<16s}"
    )
    results = []
    for position, outcome in enumerate(DECLARED_OUTCOMES, start=1):
        statistic = float(observed[position - 1])
        p_family = family_p_value(statistic, maxima)
        significant = p_family <= FAMILY_ALPHA
        verdict = "significant" if significant else "not significant"
        results.append((outcome, statistic, p_family, verdict))
        print(
            f"{position:<3d}{outcome:<34s}{abs(statistic):>9.3f}{p_family:>10.4f}"
            f"{'  ':2s}{verdict:<16s}"
        )
    print()

    print("Detail for each declared outcome")
    print("-" * 78)
    for position, (outcome, statistic, p_family, verdict) in enumerate(
        results, start=1
    ):
        n_at_least = int(np.sum(maxima >= abs(statistic)))
        direction = "higher" if statistic > 0 else "lower"
        print(f"{position:d}. {outcome}")
        print(
            f"   Observed Welch t (full minus deficit): {statistic:+.3f}  "
            f"(full irrigation {direction})"
        )
        print(
            f"   Family maxima at least as large in absolute size: "
            f"{n_at_least:d} of {N_SHUFFLES:d}"
        )
        print(
            f"   Family-wise p-value (add-one estimator): {p_family:.4f}  "
            f"-> {verdict} at the {FAMILY_ALPHA:.2f} family level"
        )
        print()


if __name__ == "__main__":
    main()
