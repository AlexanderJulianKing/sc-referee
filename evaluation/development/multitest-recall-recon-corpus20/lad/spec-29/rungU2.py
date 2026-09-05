"""Silvopasture versus open pasture for sheep.

One summer on one farm, 68 ewe-lamb pairs: 34 grazed in poplar-alley
silvopasture and 34 in adjacent open pasture. Six outcomes, reported in one
table.

The three animal-performance outcomes (lamb gain, ewe condition change, panting
score) are the pre-specified primary group and are corrected together with a
Bonferroni threshold. The three system outcomes (worm burden, pasture growth,
wool clip) are secondary descriptions of how the two systems ran and are read at
the plain five percent level.
"""

import pandas as pd
from scipy import stats

DATA = "data.csv"

ANIMAL_OUTCOMES = [
    ("lamb_adg_g_d", "lamb average daily gain (g/d)"),
    ("ewe_bcs_change", "ewe body condition change"),
    ("panting_score", "midday panting score"),
]

SYSTEM_OUTCOMES = [
    ("faecal_egg_count", "faecal egg count (epg)"),
    ("pasture_growth_kg_ha_d", "pasture growth (kg DM/ha/d)"),
    ("wool_yield_kg", "wool clip per ewe (kg)"),
]

ALPHA = 0.05
N_ANIMAL = 3
ANIMAL_THRESHOLD = ALPHA / N_ANIMAL  # Bonferroni over the three primary outcomes


def compare(open_df, silvo_df, col):
    a = open_df[col].to_numpy()
    b = silvo_df[col].to_numpy()
    test = stats.ttest_ind(a, b, equal_var=False)
    return a.mean(), b.mean(), test.pvalue


def main():
    df = pd.read_csv(DATA)
    open_df = df[df["system"] == "open"]
    silvo_df = df[df["system"] == "silvopasture"]

    print("Silvopasture versus open pasture, one summer")
    print("n open = %d, n silvopasture = %d" % (len(open_df), len(silvo_df)))
    print()
    print("Animal-performance group: Bonferroni threshold %.2f / %d = %.5f"
          % (ALPHA, N_ANIMAL, ANIMAL_THRESHOLD))
    print("System group: threshold %.2f" % ALPHA)
    print()

    header = "%-32s %10s %14s %12s %14s" % (
        "outcome", "open", "silvopasture", "p", "significance")
    print(header)
    print("-" * len(header))

    rows = []
    for col, label in ANIMAL_OUTCOMES:
        m_open, m_silvo, p = compare(open_df, silvo_df, col)
        rows.append((label, m_open, m_silvo, p, p < ALPHA))
    for col, label in SYSTEM_OUTCOMES:
        m_open, m_silvo, p = compare(open_df, silvo_df, col)
        rows.append((label, m_open, m_silvo, p, p < ALPHA))

    for label, m_open, m_silvo, p, significant in rows:
        print("%-32s %10.3f %14.3f %12.4g %14s" % (
            label, m_open, m_silvo, p,
            "significant" if significant else "not significant"))


if __name__ == "__main__":
    main()
