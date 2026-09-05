"""Ski-piste disturbance and alpine marmots: two-group comparison of five declared outcomes.

Reads marmots.csv (one row per adult marmot, 29 piste-adjacent and 29 undisturbed),
compares the two colony types on each of the five pre-declared outcomes with a Welch
two-sample t-test for independent samples, and prints group means and standard deviations.

The first three declared outcomes (body mass, faecal glucocorticoid metabolites,
emergence day) are the headline family: their p-values are multiplied here by the number
of comparisons in the declared family (5) and capped at 1, and the corrected values are
judged against 0.05. The fourth and fifth declared outcomes (vigilance, ectoparasite
count) are pre-declared questions in their own right and are judged on their raw p-values
against 0.05.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

CSV_PATH = Path(__file__).resolve().parent / "marmots.csv"

GROUP_COL = "disturbance_group"
PISTE = "piste_adjacent"
UNDISTURBED = "undisturbed"

ALPHA = 0.05
FAMILY_SIZE = 5  # number of comparisons in the declared family of outcomes

# (column, label, unit, decimals used when reporting means and SDs)
OUTCOMES = [
    ("body_mass_kg", "Pre-hibernation body mass", "kg", 2),
    ("fgm_ng_per_g", "Faecal glucocorticoid metabolites", "ng/g", 1),
    ("emergence_doy", "Spring emergence date", "day of year", 1),
    ("vigilance_pct", "Vigilance time", "% of observation period", 1),
    ("ectoparasite_count", "Ectoparasite count", "parasites", 1),
]

HEADLINE = [name for name, *_ in OUTCOMES[:3]]


def load_data(path=CSV_PATH):
    df = pd.read_csv(path)
    assert df[GROUP_COL].isin([PISTE, UNDISTURBED]).all()
    assert not df.isna().any().any()
    return df


def compare(df, column):
    """Welch two-sample t-test plus per-group mean and SD (sample SD, ddof=1)."""
    piste = df.loc[df[GROUP_COL] == PISTE, column].astype(float)
    undist = df.loc[df[GROUP_COL] == UNDISTURBED, column].astype(float)
    t_stat, p_raw = stats.ttest_ind(piste, undist, equal_var=False)
    return {
        "column": column,
        "n_piste": int(piste.size),
        "n_undisturbed": int(undist.size),
        "mean_piste": float(piste.mean()),
        "sd_piste": float(piste.std(ddof=1)),
        "mean_undisturbed": float(undist.mean()),
        "sd_undisturbed": float(undist.std(ddof=1)),
        "difference": float(piste.mean() - undist.mean()),
        "t": float(t_stat),
        "p_raw": float(p_raw),
    }


def main():
    df = load_data()

    print("Data")
    print(f"  rows: {len(df)}")
    print(f"  {PISTE}: {int((df[GROUP_COL] == PISTE).sum())}")
    print(f"  {UNDISTURBED}: {int((df[GROUP_COL] == UNDISTURBED).sum())}")
    print(f"  unique marmot_id: {df['marmot_id'].nunique()}")
    print()

    results = []
    for column, label, unit, decimals in OUTCOMES:
        res = compare(df, column)
        res["label"] = label
        res["unit"] = unit
        res["decimals"] = decimals
        if column in HEADLINE:
            # Correct by hand: multiply by the family size, cap at one.
            res["p_corrected"] = min(res["p_raw"] * FAMILY_SIZE, 1.0)
            res["significant"] = res["p_corrected"] < ALPHA
        else:
            res["p_corrected"] = None
            res["significant"] = res["p_raw"] < ALPHA
        results.append(res)

    print("Group summaries (mean +/- SD)")
    for r in results:
        d = r["decimals"]
        print(
            f"  {r['label']} ({r['unit']}): "
            f"piste_adjacent {r['mean_piste']:.{d}f} +/- {r['sd_piste']:.{d}f} "
            f"(n={r['n_piste']}); "
            f"undisturbed {r['mean_undisturbed']:.{d}f} +/- {r['sd_undisturbed']:.{d}f} "
            f"(n={r['n_undisturbed']}); "
            f"difference {r['difference']:+.{d}f}"
        )
    print()

    print(f"Headline outcomes 1-3 (raw p x {FAMILY_SIZE}, capped at 1, judged at {ALPHA})")
    for r in results[:3]:
        verdict = "significant" if r["significant"] else "not significant"
        print(
            f"  {r['label']}: t = {r['t']:.3f}, raw p = {r['p_raw']:.4f}, "
            f"corrected p = {r['p_corrected']:.4f} -> {verdict}"
        )
    print()

    print(f"Outcomes 4-5 (raw p judged at {ALPHA})")
    for r in results[3:]:
        verdict = "significant" if r["significant"] else "not significant"
        print(f"  {r['label']}: t = {r['t']:.3f}, p = {r['p_raw']:.4f} -> {verdict}")

    return results


if __name__ == "__main__":
    main()
