"""Silver vs foam dressing in neuropathic diabetic foot ulcers.

Twelve-week vascular clinic comparison, 112 patients allocated at their first
visit. Five outcomes were recorded for every patient; each is compared between
the two dressings with a two-sample t-test.
"""

import pandas as pd
from scipy import stats

# Significance level for the study.
ALPHA = 0.05

OUTCOMES = [
    ("time_to_heal_days", "Time to healing (days, censored at 84)"),
    ("area_reduction_pct", "Ulcer area reduction at 12 weeks (%)"),
    ("infection_episodes", "Infection episodes in 12 weeks"),
    ("pain_score", "Pain at dressing change (0-10)"),
    ("dressing_changes", "Dressing changes in 12 weeks"),
]


def show_p(p):
    return "<0.0001" if p < 0.0001 else "%.4f" % p


def main():
    df = pd.read_csv("data.csv")
    foam = df[df["dressing"] == "foam"]
    silver = df[df["dressing"] == "silver"]

    print("Diabetic foot ulcer dressing comparison")
    print("n = %d foam, %d silver" % (len(foam), len(silver)))
    print("Significance level: alpha = %.2f" % ALPHA)
    print()
    print("%-46s %10s %10s %12s  %s" % ("Outcome", "foam", "silver", "p-value", "Verdict"))
    print("-" * 96)

    for column, label in OUTCOMES:
        a = foam[column]
        b = silver[column]
        _, p = stats.ttest_ind(a, b)
        verdict = "significant" if p < ALPHA else "not significant"
        print(f"{label:-46s} {a.mean():10.2f} {b.mean():10.2f} {show_p(p):12s}  {verdict}")


if __name__ == "__main__":
    main()
