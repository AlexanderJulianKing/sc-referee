"""Microplastics in blue mussels: outfall bay vs reference bay.

The two bays are selected with boolean masks built once from the bay column and
reused for every outcome. Each outcome gets its own two-sample t-test and is
judged on its own p-value against 0.05. No family-wide adjustment.
"""

import pandas as pd
from scipy import stats

CUTOFF = 0.05

OUTCOMES = [
    ("particles_per_g", "microplastic particles per g"),
    ("mean_particle_um", "mean particle size (um)"),
    ("fibre_fraction_pct", "fibre fraction (%)"),
    ("condition_index", "condition index"),
    ("glutathione_s_transferase", "GST activity (nmol/min/mg)"),
]


def main():
    df = pd.read_csv("data.csv")

    is_reference = df["bay"] == "reference"
    is_outfall = df["bay"] == "outfall"

    print("Blue mussel survey, one sampling week")
    print(f"  reference bay : {int(is_reference.sum())} mussels")
    print(f"  outfall bay   : {int(is_outfall.sum())} mussels")
    print()

    header = (f"{'outcome':30s} {'reference':>11s} {'outfall':>11s} "
              f"{'p':>9s}  verdict")
    print(header)
    print("-" * len(header))

    n_sig = 0
    for col, label in OUTCOMES:
        ref_vals = df.loc[is_reference, col]
        out_vals = df.loc[is_outfall, col]

        _, p = stats.ttest_ind(ref_vals, out_vals)
        significant = p < CUTOFF
        n_sig += significant
        verdict = "significant" if significant else "not significant"

        print(f"{label:30s} {ref_vals.mean():11.3f} {out_vals.mean():11.3f} "
              f"{p:9.5f}  {verdict}")

    print()
    print(f"{n_sig} of {len(OUTCOMES)} outcomes differ between bays at p < {CUTOFF:.2f}.")


if __name__ == "__main__":
    main()
