"""Drip versus furrow irrigation in cotton: six agronomic outcomes.

One season, 72 harvest quadrats (36 furrow, 36 drip) on adjacent fields of the
same soil series and cultivar. The six outcome columns are treated as one
family and the whole family is corrected together.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA = "data.csv"
ALPHA = 0.05

OUTCOMES = [
    ("lint_yield_kg_ha", "lint yield (kg/ha)"),
    ("water_applied_mm", "water applied (mm)"),
    ("water_use_efficiency_kg_ha_mm", "water use efficiency (kg/ha/mm)"),
    ("fibre_length_mm", "fibre length (mm)"),
    ("micronaire", "micronaire"),
    ("soil_salinity_ds_m", "soil salinity (dS/m)"),
]


def main():
    df = pd.read_csv(DATA)
    furrow = df[df["irrigation"] == "furrow"]
    drip = df[df["irrigation"] == "drip"]

    print("Drip versus furrow irrigation, upland cotton")
    print("n furrow = %d, n drip = %d" % (len(furrow), len(drip)))
    print()

    names = []
    raw_p = []
    means_furrow = []
    means_drip = []

    for col, label in OUTCOMES:
        a = furrow[col].to_numpy()
        b = drip[col].to_numpy()
        # Welch two-sample t-test: the two systems are separate fields and there
        # is no reason to assume equal variances.
        result = stats.ttest_ind(a, b, equal_var=False)
        names.append(label)
        raw_p.append(result.pvalue)
        means_furrow.append(a.mean())
        means_drip.append(b.mean())

    # All six outcomes were measured on the same quadrats and are reported
    # together, so they form one family and are corrected in one call.
    reject, p_adj, _, _ = multipletests(raw_p, alpha=ALPHA, method="fdr_bh")
    method_name = "Benjamini-Hochberg step-up FDR control"

    print("Multiplicity correction: %s" % method_name)
    print("Family: all %d agronomic outcomes, corrected in one step at "
          "q = %.2f" % (len(OUTCOMES), ALPHA))
    print()

    header = "%-32s %10s %10s %10s %12s %14s" % (
        "outcome", "furrow", "drip", "raw p", "adjusted p", "BH decision")
    print(header)
    print("-" * len(header))
    for i, label in enumerate(names):
        print("%-32s %10.3f %10.3f %10.4g %12.4g %14s" % (
            label,
            means_furrow[i],
            means_drip[i],
            raw_p[i],
            p_adj[i],
            "survives" if reject[i] else "not supported",
        ))
    print()
    print("Raw p-values are shown for transparency only. Every claim below is "
          "based on the adjusted value.")
    survivors = [names[i] for i in range(len(names)) if reject[i]]
    if survivors:
        print("Differences supported after correction: " + "; ".join(survivors))
    else:
        print("No outcome survives correction.")


if __name__ == "__main__":
    main()
