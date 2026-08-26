"""Road salt runoff and roadside soil: salted arterial route vs unsalted rural route.

Five soil outcomes, one two-sample t-test each. Every p-value is rounded to
three decimal places as soon as it comes back from the test, and only that
rounded value is carried forward into the comparisons, the printed verdicts and
the summary table. No family-wide adjustment is applied.
"""

import pandas as pd
from scipy import stats

CUTOFF = 0.05

OUTCOMES = [
    ("soil_chloride_mg_kg", "soil chloride (mg/kg)"),
    ("electrical_conductivity_ds_m", "electrical conductivity (dS/m)"),
    ("sodium_adsorption_ratio", "sodium adsorption ratio"),
    ("soil_ph", "soil pH"),
    ("earthworm_count", "earthworms per core"),
]


def main():
    df = pd.read_csv("data.csv")
    unsalted = df[df["route_type"] == "unsalted"]
    salted = df[df["route_type"] == "salted"]

    print("Roadside soil survey, end of winter")
    print(f"  unsalted rural route   : {len(unsalted)} composite cores")
    print(f"  salted arterial route  : {len(salted)} composite cores")
    print()

    table = []
    for col, label in OUTCOMES:
        a = unsalted[col]
        b = salted[col]
        _, p = stats.ttest_ind(a, b)
        p = round(p, 3)   # keep the rounded value only, from here on

        if p < CUTOFF:
            verdict = "significant"
        else:
            verdict = "not significant"

        print(f"{label}")
        print(f"  unsalted mean = {a.mean():.3f}    salted mean = {b.mean():.3f}")
        print(f"  p = {p:.3f} -> {verdict} at the {CUTOFF:.2f} level")
        print()

        table.append((label, a.mean(), b.mean(), p, verdict))

    header = f"{'outcome':32s} {'unsalted':>10s} {'salted':>10s} {'p':>7s}  verdict"
    print(header)
    print("-" * len(header))
    for label, mean_a, mean_b, p, verdict in table:
        print(f"{label:32s} {mean_a:10.3f} {mean_b:10.3f} {p:7.3f}  {verdict}")
    print()

    n_sig = sum(1 for row in table if row[4] == "significant")
    print(f"{n_sig} of {len(table)} outcomes differ between route types "
          f"at p < {CUTOFF:.2f}, uncorrected.")


if __name__ == "__main__":
    main()
