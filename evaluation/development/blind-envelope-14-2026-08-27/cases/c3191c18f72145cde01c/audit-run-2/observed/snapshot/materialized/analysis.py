"""Substrate comparison for the pot-grown cyclamen trial.

Reads `cyclamen_substrate_trial.csv` (one row per plant) and compares the two
substrate groups on the five pre-declared plant-level outcomes.

Family-wise error across the five declared outcomes is controlled with a
label-shuffling (permutation) procedure written out in full below, not with a
packaged multiplicity correction.
"""

import csv
import math
import os
import random

# ---------------------------------------------------------------------------
# Fixed analysis constants, set in advance.
# ---------------------------------------------------------------------------

DATA_FILE = "cyclamen_substrate_trial.csv"

GROUP_COLUMN = "substrate"
GROUP_A = "peat_based"   # conventional peat-based substrate
GROUP_B = "peat_free"    # coir and wood fibre blend

# The five outcomes exactly as declared before potting, in the declared order.
OUTCOMES = [
    "canopy_diameter_cm",
    "open_flower_count",
    "shoot_dry_mass_g",
    "spad_reading",
    "days_to_first_flower",
]

# Number of label shuffles, fixed in advance.
N_SHUFFLES = 5000

# Fixed random seed so the run reproduces exactly.
RANDOM_SEED = 20260826

# Significance threshold applied to the shuffle-based p-values.
ALPHA = 0.05


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_rows(path):
    """Return the CSV as a list of dicts, one dict per plant."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("no data rows found in %s" % path)
    return rows


def build_arrays(rows):
    """Return (labels, values) where values[outcome] is a list aligned to labels."""
    labels = [row[GROUP_COLUMN] for row in rows]

    unexpected = sorted(set(labels) - {GROUP_A, GROUP_B})
    if unexpected:
        raise ValueError("unexpected %s values: %s" % (GROUP_COLUMN, unexpected))

    values = {}
    for outcome in OUTCOMES:
        column = []
        for row in rows:
            cell = row[outcome]
            if cell is None or cell.strip() == "":
                raise ValueError("blank cell in column %s" % outcome)
            column.append(float(cell))
        values[outcome] = column
    return labels, values


# ---------------------------------------------------------------------------
# Two-sample test statistic
# ---------------------------------------------------------------------------

def mean(sample):
    return sum(sample) / len(sample)


def variance(sample, sample_mean):
    """Unbiased (n - 1) sample variance."""
    n = len(sample)
    if n < 2:
        raise ValueError("need at least two observations to estimate a variance")
    return sum((x - sample_mean) ** 2 for x in sample) / (n - 1)


def welch_t(values, labels):
    """Welch's two-sample t statistic for GROUP_B minus GROUP_A.

    Welch's form does not assume the two groups share a variance, which suits
    plant measurements where one substrate can be both shifted and more
    variable than the other. The same statistic is used for every outcome and
    for every shuffle, so the observed values and the shuffled values are on
    one comparable scale.
    """
    a = [v for v, lab in zip(values, labels) if lab == GROUP_A]
    b = [v for v, lab in zip(values, labels) if lab == GROUP_B]

    mean_a = mean(a)
    mean_b = mean(b)
    se_squared = variance(a, mean_a) / len(a) + variance(b, mean_b) / len(b)
    if se_squared <= 0.0:
        return 0.0
    return (mean_b - mean_a) / math.sqrt(se_squared)


# ---------------------------------------------------------------------------
# Observed results
# ---------------------------------------------------------------------------

def observed_results(values, labels):
    """Group means, difference, and observed statistic for each declared outcome."""
    results = []
    for outcome in OUTCOMES:
        column = values[outcome]
        a = [v for v, lab in zip(column, labels) if lab == GROUP_A]
        b = [v for v, lab in zip(column, labels) if lab == GROUP_B]
        mean_a = mean(a)
        mean_b = mean(b)
        results.append(
            {
                "outcome": outcome,
                "n_a": len(a),
                "n_b": len(b),
                "mean_a": mean_a,
                "mean_b": mean_b,
                "difference": mean_b - mean_a,
                "statistic": welch_t(column, labels),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Label-shuffling reference distribution of family maxima
# ---------------------------------------------------------------------------

def family_maximum_distribution(values, labels):
    """Build the reference distribution of family-maximum statistics.

    The substrate labels are shuffled across all plants at once. Because each
    plant carries its whole row of five outcomes through the shuffle, the real
    relationships between the outcomes are preserved in every shuffled data
    set. For each shuffle the statistic is recomputed for all five declared
    outcomes and only the single largest absolute statistic across the family
    is kept, giving a distribution of N_SHUFFLES family maxima.
    """
    rng = random.Random(RANDOM_SEED)
    shuffled = list(labels)
    maxima = []
    for _ in range(N_SHUFFLES):
        rng.shuffle(shuffled)
        largest = 0.0
        for outcome in OUTCOMES:
            statistic = abs(welch_t(values[outcome], shuffled))
            if statistic > largest:
                largest = statistic
        maxima.append(largest)
    return maxima


def family_p_value(observed_statistic, maxima):
    """Share of shuffles whose family maximum is at least as extreme."""
    target = abs(observed_statistic)
    at_least_as_extreme = sum(1 for m in maxima if m >= target)
    return at_least_as_extreme / len(maxima)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
    rows = load_rows(path)
    labels, values = build_arrays(rows)

    results = observed_results(values, labels)
    maxima = family_maximum_distribution(values, labels)

    for result in results:
        result["p_value"] = family_p_value(result["statistic"], maxima)
        result["significant"] = result["p_value"] < ALPHA

    n_a = labels.count(GROUP_A)
    n_b = labels.count(GROUP_B)

    print("Cyclamen substrate trial: comparison of two growing substrates")
    print("Plants: %d total (%s n=%d, %s n=%d)" % (len(labels), GROUP_A, n_a, GROUP_B, n_b))
    print("Declared outcome family: %d outcomes, in the declared order" % len(OUTCOMES))
    print("Label shuffles: %d (fixed in advance), random seed %d" % (N_SHUFFLES, RANDOM_SEED))
    print("Statistic: Welch two-sample t, %s minus %s" % (GROUP_B, GROUP_A))
    print(
        "P-value: share of the %d family maxima that are at least as extreme as the "
        "outcome's observed |t|" % N_SHUFFLES
    )
    print("Significance threshold: p < %.2f" % ALPHA)
    print()

    header = "%-22s %12s %12s %12s %10s %9s  %s" % (
        "outcome",
        "mean " + GROUP_A,
        "mean " + GROUP_B,
        "difference",
        "t",
        "p",
        "verdict",
    )
    print(header)
    print("-" * len(header))
    for result in results:
        print(
            "%-22s %12.3f %12.3f %12.3f %10.3f %9.4f  %s"
            % (
                result["outcome"],
                result["mean_a"],
                result["mean_b"],
                result["difference"],
                result["statistic"],
                result["p_value"],
                "significant" if result["significant"] else "not significant",
            )
        )

    print()
    print(
        "Family-maximum reference distribution: min %.3f, median %.3f, "
        "95th percentile %.3f, max %.3f"
        % (
            min(maxima),
            sorted(maxima)[len(maxima) // 2],
            sorted(maxima)[int(0.95 * len(maxima))],
            max(maxima),
        )
    )


if __name__ == "__main__":
    main()
