"""Reduced-rate vs full-rate fungicide programme for black scurf in seed potatoes.

Six outcomes are compared across the plots. Multiplicity is handled with a
label-shuffling maximum-statistic procedure written out here rather than a
packaged correction: the null distribution of the largest absolute statistic over
the whole family of six is built by reshuffling the programme labels, and each
outcome's adjusted p-value is read off that one distribution.
"""

import numpy as np
import pandas as pd
from scipy import stats

DATA = "data.csv"
GROUP = "programme"
FULL = "full_rate"
REDUCED = "reduced_rate"

OUTCOMES = [
    "marketable_yield_t_ha",
    "black_scurf_incidence_pct",
    "stem_canker_index",
    "tuber_number_per_plant",
    "mean_tuber_weight_g",
    "fungicide_cost_gbp_ha",
]

N_SHUFFLES = 4000
SEED = 71042
ALPHA = 0.05


def statistics(values, is_reduced):
    """Welch t statistic for every outcome under one labelling of the plots."""
    reduced = values[is_reduced]
    full = values[~is_reduced]
    return stats.ttest_ind(reduced, full, axis=0, equal_var=False).statistic


def main():
    plots = pd.read_csv(DATA)
    values = plots[OUTCOMES].to_numpy()
    is_reduced = (plots[GROUP] == REDUCED).to_numpy()

    print("Plots: %d (%s %d, %s %d)" % (
        len(plots),
        FULL, int((~is_reduced).sum()),
        REDUCED, int(is_reduced.sum()),
    ))
    print("Multiplicity: label-shuffling maximum-statistic procedure over all "
          "%d outcomes" % len(OUTCOMES))
    print("Shuffles: %d" % N_SHUFFLES)
    print("Random seed: %d" % SEED)
    print("Family-wide level: %.2f" % ALPHA)
    print()

    observed = statistics(values, is_reduced)

    rng = np.random.default_rng(SEED)
    maxima = np.empty(N_SHUFFLES)
    for b in range(N_SHUFFLES):
        shuffled = rng.permutation(is_reduced)
        maxima[b] = np.max(np.abs(statistics(values, shuffled)))

    adjusted = np.array([
        float(np.mean(maxima >= abs(t))) for t in observed
    ])

    header = "%-27s %10s %10s %8s %11s  %s" % (
        "outcome", FULL, REDUCED, "t", "adj. p", "verdict")
    print(header)
    print("-" * len(header))

    for name, t, p in zip(OUTCOMES, observed, adjusted):
        full_mean = plots.loc[~is_reduced, name].astype(float).mean()
        reduced_mean = plots.loc[is_reduced, name].astype(float).mean()
        verdict = "significant" if p < ALPHA else "not significant"
        print("%-27s %10.2f %10.2f %8.2f %11.4f  %s" % (
            name, full_mean, reduced_mean, t, p, verdict))

    print()
    print("Adjusted p is the fraction of the %d shuffle maxima that reach or "
          "exceed" % N_SHUFFLES)
    print("the outcome's observed absolute t. Statistics are %s minus %s." % (
        REDUCED, FULL))
    print("Largest shuffle maximum observed: %.2f; 95th percentile: %.2f" % (
        maxima.max(), np.percentile(maxima, 95)))

    called = [n for n, p in zip(OUTCOMES, adjusted) if p < ALPHA]
    print("Significant at the family-wide level: %s" % (", ".join(called) or "none"))


if __name__ == "__main__":
    main()
