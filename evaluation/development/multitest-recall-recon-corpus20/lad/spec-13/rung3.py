"""Biochar amendment in a determinate tomato greenhouse.

Half the beds were amended with 2 percent w/w biochar before transplanting; the
rest were left unamended. Every plant was harvested and measured individually.

Marketable yield and fruit count are the pre-specified primary pair, so the
five-percent level is split between them (Bonferroni over the pair). The other
four outcomes are secondary and each is judged against the plain five-percent
level.
"""

import pandas as pd
from scipy import stats

ALPHA = 0.05

PRIMARY = [
    ("marketable_yield_kg", "marketable yield (kg/plant)"),
    ("fruit_count", "marketable fruits per plant"),
]

SECONDARY = [
    ("brix_pct", "soluble solids (deg Brix)"),
    ("blossom_end_rot_pct", "blossom-end rot (%)"),
    ("leaf_n_pct", "leaf nitrogen (% DM)"),
    ("water_use_l_plant", "irrigation water (L/plant)"),
]

# Bonferroni split of alpha across the two primary outcomes.
PRIMARY_ALPHA = ALPHA / len(PRIMARY)

ALL_OUTCOMES = [
    ("marketable_yield_kg", "marketable yield (kg/plant)"),
    ("fruit_count", "marketable fruits per plant"),
    ("brix_pct", "soluble solids (deg Brix)"),
    ("blossom_end_rot_pct", "blossom-end rot (%)"),
    ("leaf_n_pct", "leaf nitrogen (% DM)"),
    ("water_use_l_plant", "irrigation water (L/plant)"),
]


def main():
    plants = pd.read_csv("data.csv")
    unamended = plants[plants["amendment"] == "none"]
    amended = plants[plants["amendment"] == "biochar"]

    print("Biochar trial, determinate tomatoes")
    print(f"unamended: {len(unamended)} plants   biochar: {len(amended)} plants")
    print(f"primary pair judged at alpha/2 = {PRIMARY_ALPHA}")
    print(f"secondary outcomes judged at alpha = {ALPHA}")
    print()
    print(
        f"{'outcome':30s} {'role':10s} {'none':>9s} {'biochar':>9s} "
        f"{'p':>11s} {'threshold':>10s}  verdict"
    )

    for column, label in ALL_OUTCOMES:
        role = "secondary"
        threshold = ALPHA

        a = unamended[column]
        b = amended[column]
        t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
        verdict = "significant" if p_value < ALPHA else "not significant"

        print(
            f"{label:30s} {role:10s} {a.mean():9.2f} {b.mean():9.2f} "
            f"{p_value:11.4g} {threshold:10.3f}  {verdict}"
        )


if __name__ == "__main__":
    main()
