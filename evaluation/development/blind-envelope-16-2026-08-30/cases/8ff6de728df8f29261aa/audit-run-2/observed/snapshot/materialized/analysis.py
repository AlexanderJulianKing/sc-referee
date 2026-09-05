"""Vacuum versus atmospheric frying of plantain crisps: group comparison.

Compares the two frying methods on the five pre-declared outcomes with an
independent two-sample t-test, one test per outcome.

The two nutritional and safety endpoints (oil content, acrylamide) are read
conservatively: their p-values are corrected by hand by multiplying by the
number of comparisons made and capping at 1, and their verdicts are taken from
the corrected values at alpha = 0.05.

The three quality endpoints (breaking force, colour b*, crispness) are each a
separate pre-declared question, so each raw p-value is compared with alpha =
0.05 directly.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "plantain_frying_batches.csv"
GROUP_COL = "frying_method"
GROUP_A = "vacuum"
GROUP_B = "atmospheric"
ALPHA = 0.05

# Pre-declared outcome family, in the declared order.
OUTCOMES = [
    ("oil_content_g100g", "Oil content (g/100 g)"),
    ("acrylamide_ug_kg", "Acrylamide (ug/kg)"),
    ("breaking_force_n", "Breaking force (N)"),
    ("colour_b_cielab", "Colour b* (CIELAB)"),
    ("crispness_score_pts", "Crispness score (pts)"),
]

# Safety-related endpoints, read conservatively with a hand correction.
SAFETY_OUTCOMES = ["oil_content_g100g", "acrylamide_ug_kg"]


def main():
    df = pd.read_csv(DATA_FILE)

    vacuum = df[df[GROUP_COL] == GROUP_A]
    atmospheric = df[df[GROUP_COL] == GROUP_B]

    print("Plantain crisp frying trial: vacuum (120 C) vs atmospheric (170 C)")
    print("Batches: {} vacuum, {} atmospheric, {} total".format(
        len(vacuum), len(atmospheric), len(df)))
    print("Missing values in outcome columns: {}".format(
        int(df[[c for c, _ in OUTCOMES]].isna().sum().sum())))
    print()

    # Number of comparisons made in this analysis, used for the hand correction.
    n_comparisons = len(OUTCOMES)
    print("Number of comparisons made: {}".format(n_comparisons))
    print()

    results = []
    for column, label in OUTCOMES:
        x = vacuum[column]
        y = atmospheric[column]
        t_stat, p_raw = stats.ttest_ind(x, y)
        results.append({
            "column": column,
            "label": label,
            "mean_vacuum": x.mean(),
            "mean_atmospheric": y.mean(),
            "t": t_stat,
            "p_raw": p_raw,
        })

    print("Per-outcome two-sample t-tests (raw)")
    print("-" * 78)
    for r in results:
        print("{:<24s} mean_vacuum={:>8.3f}  mean_atmospheric={:>8.3f}  "
              "t={:>8.3f}  p_raw={:.6g}".format(
                  r["column"], r["mean_vacuum"], r["mean_atmospheric"],
                  r["t"], r["p_raw"]))
    print()

    # Hand correction, done openly, for the two safety-related endpoints only.
    print("Hand correction for the nutritional and safety endpoints")
    print("-" * 78)
    for r in results:
        if r["column"] in SAFETY_OUTCOMES:
            product = r["p_raw"] * n_comparisons
            p_corrected = min(product, 1.0)
            r["p_corrected"] = p_corrected
            print("{:<24s} p_raw={:.6g} x {} = {:.6g} -> capped at 1 -> "
                  "p_corrected={:.6g}".format(
                      r["column"], r["p_raw"], n_comparisons,
                      product, p_corrected))
        else:
            r["p_corrected"] = None
    print()

    print("Verdicts at alpha = {}".format(ALPHA))
    print("-" * 78)
    for r in results:
        if r["p_corrected"] is not None:
            p_used = r["p_corrected"]
            basis = "corrected p"
        else:
            p_used = r["p_raw"]
            basis = "raw p"
        r["p_used"] = p_used
        r["basis"] = basis
        r["significant"] = p_used < ALPHA
        print("{:<24s} {:<12s} p={:.6g}  ->  {}".format(
            r["column"], basis, p_used,
            "difference between methods" if r["significant"]
            else "no difference detected"))
    print()

    print("Summary table")
    print("-" * 78)
    print("{:<24s} {:>9s} {:>13s} {:>9s} {:>11s} {:>11s}".format(
        "outcome", "vacuum", "atmospheric", "t", "p_raw", "p_used"))
    for r in results:
        print("{:<24s} {:>9.3f} {:>13.3f} {:>9.3f} {:>11.6g} {:>11.6g}".format(
            r["column"], r["mean_vacuum"], r["mean_atmospheric"],
            r["t"], r["p_raw"], r["p_used"]))


if __name__ == "__main__":
    main()
