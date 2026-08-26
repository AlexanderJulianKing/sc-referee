"""Heritage vs commercial starter culture, one week of artisan yoghurt production.

The six quality outcomes are treated as one panel. Nothing is said about an
individual outcome until the whole panel has cleared a permutation screen, so the
script always prints the gate result first.
"""

import numpy as np
import pandas as pd
from scipy import stats

DATA = "data.csv"
GROUP = "culture"
REFERENCE = "commercial"
COMPARATOR = "heritage"

OUTCOMES = [
    "ph_day1",
    "titratable_acidity_pct",
    "syneresis_pct",
    "viscosity_mpa_s",
    "viable_count_log",
    "panel_liking",
]

N_PERM = 2000
SEED = 20260415
ALPHA = 0.05


def panel_distance(z, mask):
    """Squared length of the difference between the two group mean vectors.

    `z` is the standardised outcome matrix (pots x outcomes) and `mask` is a
    boolean vector that is True for the pots assigned to the comparator group.
    """
    diff = z[mask].mean(axis=0) - z[~mask].mean(axis=0)
    return float(np.sum(diff ** 2))


def main():
    pots = pd.read_csv(DATA)
    z = pots[OUTCOMES].to_numpy()
    z = (z - z.mean(axis=0)) / z.std(axis=0)

    mask = (pots[GROUP] == COMPARATOR).to_numpy()

    observed = panel_distance(z, mask)

    rng = np.random.default_rng(SEED)
    null = np.empty(N_PERM)
    for b in range(N_PERM):
        null[b] = panel_distance(z, rng.permutation(mask))

    p_panel = float(np.mean(null >= observed))

    print("Panel-level screen (all six outcomes together)")
    print("  pots: %d (%s %d, %s %d)" % (
        len(pots),
        REFERENCE, int((~mask).sum()),
        COMPARATOR, int(mask.sum()),
    ))
    print("  statistic: summed squared difference of standardised mean vectors")
    print("  observed statistic = %.4f" % observed)
    print("  label permutations = %d (seed %d)" % (N_PERM, SEED))
    print("  permutation p-value = %.4f" % p_panel)

    if p_panel >= ALPHA:
        print()
        print("  Gate CLOSED at alpha = %.2f." % ALPHA)
        print("  The panel showed no overall culture effect, so no individual")
        print("  outcome is tested and no per-outcome verdict is reported.")
        return

    print()
    print("  Gate OPEN at alpha = %.2f: proceeding to the six outcomes." % ALPHA)
    print()

    header = "%-24s %12s %12s %10s %9s  %s" % (
        "outcome", REFERENCE, COMPARATOR, "diff", "p", "verdict")
    print(header)
    print("-" * len(header))

    for name in OUTCOMES:
        ref = pots.loc[~mask, name].to_numpy()
        cmp_ = pots.loc[mask, name].to_numpy()
        result = stats.ttest_ind(cmp_, ref, equal_var=False)
        diff = cmp_.mean() - ref.mean()
        verdict = "different" if result.pvalue < ALPHA else "no difference"
        print("%-24s %12.3f %12.3f %10.3f %9.4f  %s" % (
            name, ref.mean(), cmp_.mean(), diff, result.pvalue, verdict))

    print()
    print("Differences are %s minus %s." % (COMPARATOR, REFERENCE))


if __name__ == "__main__":
    main()
