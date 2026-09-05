"""Hedgerow cutting regime analysis.

Compares annually cut and rotationally cut hedge sections on the five
pre-declared outcomes, then corrects the five raw p-values together as one
family at a family-wise error level of 0.05.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA_FILE = "hedge_sections.csv"
GROUP_COL = "cut_regime"
GROUP_A = "annual"
GROUP_B = "rotational"
ALPHA = 0.05

# Declared outcome family, in the pre-declared order.
OUTCOMES = [
    "berry_mass_gpm",
    "stem_density_spm",
    "plant_richness_spp",
    "basal_gap_pct",
    "invert_biomass_mgpm",
]


def main():
    data = pd.read_csv(DATA_FILE)

    annual = data[data[GROUP_COL] == GROUP_A]
    rotational = data[data[GROUP_COL] == GROUP_B]

    print(f"rows: {len(data)}")
    print(f"{GROUP_A}: {len(annual)}   {GROUP_B}: {len(rotational)}")
    print()

    mean_annual = []
    mean_rotational = []
    raw_p = []

    for outcome in OUTCOMES:
        a = annual[outcome]
        b = rotational[outcome]
        result = stats.ttest_ind(a, b)
        mean_annual.append(a.mean())
        mean_rotational.append(b.mean())
        raw_p.append(result.pvalue)

    # The five declared outcomes are one family: correct them in a single call
    # and accept the routine's default adjustment.
    reject, adjusted_p, _, _ = multipletests(raw_p, alpha=ALPHA)

    header = (
        f"{'outcome':<20} {'mean_annual':>12} {'mean_rotational':>16} "
        f"{'raw_p':>10} {'adjusted':>10} {'verdict':>16}"
    )
    print(header)
    print("-" * len(header))
    for i, outcome in enumerate(OUTCOMES):
        verdict = "significant" if reject[i] else "not significant"
        print(
            f"{outcome:<20} {mean_annual[i]:>12.2f} {mean_rotational[i]:>16.2f} "
            f"{raw_p[i]:>10.4f} {adjusted_p[i]:>10.4f} {verdict:>16}"
        )


if __name__ == "__main__":
    main()
