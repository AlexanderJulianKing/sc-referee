"""Fermented versus fresh vegetable snack: gut and inflammatory markers.

Parallel four-week study in healthy adults, 76 participants (38 per arm). Six
markers were measured at the end of the four weeks. The six markers are one
family, and the family-wise error rate is controlled across all six at once with
multipy, a package written for multiple-comparison correction.
"""

import pandas as pd
from importlib.metadata import version
from scipy import stats
from multipy.fwer import sidak

DATA = "data.csv"
ALPHA = 0.05

MARKERS = [
    ("stool_frequency_per_wk", "stool frequency (per week)"),
    ("faecal_ph", "faecal pH"),
    ("il6_pg_ml", "interleukin-6 (pg/mL)"),
    ("crp_mg_l", "C-reactive protein (mg/L)"),
    ("lactobacillus_log", "faecal lactobacilli (log10 CFU/g)"),
    ("bloating_score", "bloating score (0-10)"),
]


def main():
    df = pd.read_csv(DATA)
    fresh = df[df["arm"] == "fresh"]
    fermented = df[df["arm"] == "fermented"]

    print("Fermented versus fresh vegetables, four weeks")
    print("n fresh = %d, n fermented = %d" % (len(fresh), len(fermented)))
    print()

    labels = []
    raw_p = []
    mean_fresh = []
    mean_fermented = []

    for col, label in MARKERS:
        a = fresh[col].to_numpy()
        b = fermented[col].to_numpy()
        test = stats.ttest_ind(a, b, equal_var=False)  # Welch
        labels.append(label)
        raw_p.append(test.pvalue)
        mean_fresh.append(a.mean())
        mean_fermented.append(b.mean())

    # multipy.fwer.sidak holds the family-wise error rate at ALPHA over all six
    # markers by testing each raw p against 1 - (1 - ALPHA) ** (1 / n). It
    # returns the decisions; the matching adjusted p-value for a marker is
    # 1 - (1 - p) ** n, which is printed next to each raw value so the two agree
    # by construction.
    significant = sidak(raw_p, alpha=ALPHA)
    n = len(raw_p)
    adjusted_p = [1.0 - (1.0 - p) ** n for p in raw_p]

    print("Multiplicity control: multipy %s, Sidak correction "
          "(multipy.fwer.sidak)" % version("multipy"))
    print("Family: all %d markers. Family-wise error rate held at %.2f."
          % (n, ALPHA))
    print("Per-marker Sidak threshold: %.6f" % (1.0 - (1.0 - ALPHA) ** (1.0 / n)))
    print()

    header = "%-36s %8s %11s %12s %14s %14s" % (
        "marker", "fresh", "fermented", "raw p", "adjusted p", "decision")
    print(header)
    print("-" * len(header))
    for i, label in enumerate(labels):
        print("%-36s %8.3f %11.3f %12.4g %14.4g %14s" % (
            label, mean_fresh[i], mean_fermented[i], raw_p[i], adjusted_p[i],
            "significant" if significant[i] else "not significant"))
    print()

    findings = [labels[i] for i in range(n) if significant[i]]
    if findings:
        print("Findings (multipy decisions only): " + "; ".join(findings))
    else:
        print("No marker is significant after family-wise correction.")


if __name__ == "__main__":
    main()
