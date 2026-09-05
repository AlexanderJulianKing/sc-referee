"""Hypotonic vs isotonic oral rehydration solution in calf scours.

86 calves from cooperating dairy farms over two calving seasons. Five outcomes make
up the family. For each outcome the assumptions of the two-sample t-test are checked
first, the test is chosen on the basis of those checks, and the five resulting
p-values are then corrected together with Holm's step-down procedure at a family-wide
five percent level.
"""

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

FAMILY_ALPHA = 0.05
CHECK_ALPHA = 0.05

OUTCOMES = [
    ("time_to_resolution_h", "Time to resolution (h)"),
    ("blood_ph", "Venous blood pH at 24 h"),
    ("base_excess_mmol_l", "Base excess at 24 h (mmol/L)"),
    ("weight_change_pct", "Weight change over 72 h (%)"),
    ("serum_sodium_mmol_l", "Serum sodium at 24 h (mmol/L)"),
]


def fmt_p(p):
    return "<0.0001" if p < 0.0001 else "%.4f" % p


df = pd.read_csv("data.csv")
iso = df[df["solution"] == "isotonic"]
hyp = df[df["solution"] == "hypotonic"]

print("Oral rehydration in calf scours: %d isotonic, %d hypotonic" % (len(iso), len(hyp)))
print()
print("Assumption checks (Shapiro-Wilk per group, Levene for equal variances)")
print("-" * 78)

raw = []
choices = []

for column, label in OUTCOMES:
    a = iso[column]
    b = hyp[column]

    _, p_norm_iso = stats.shapiro(a)
    _, p_norm_hyp = stats.shapiro(b)
    _, p_var = stats.levene(a, b, center="median")

    normal = p_norm_iso >= CHECK_ALPHA and p_norm_hyp >= CHECK_ALPHA
    equal_var = p_var >= CHECK_ALPHA

    print("%s" % label)
    print("   Shapiro-Wilk isotonic  p = %s" % fmt_p(p_norm_iso))
    print("   Shapiro-Wilk hypotonic p = %s" % fmt_p(p_norm_hyp))
    print("   Levene                 p = %s" % fmt_p(p_var))

    if not normal:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        test = "Mann-Whitney U"
        reason = "at least one group departs from normality"
    elif not equal_var:
        _, p = stats.ttest_ind(a, b, equal_var=False)
        test = "Welch t-test"
        reason = "normal within groups but unequal variances"
    else:
        _, p = stats.ttest_ind(a, b)
        test = "Student t-test"
        reason = "normality and equal variances both hold"

    print("   -> %s (%s)" % (test, reason))
    print()

    raw.append(p)
    choices.append(test)

reject, adjusted, _, _ = multipletests(raw, alpha=FAMILY_ALPHA, method="holm")

print("Family of five outcomes, Holm correction at family alpha = %.2f" % FAMILY_ALPHA)
print()
print("%-30s %16s %10s %10s  %s"
      % ("Outcome", "Test", "raw p", "adj p", "Conclusion"))
print("-" * 86)
for (column, label), test, p, p_adj, sig in zip(OUTCOMES, choices, raw, adjusted, reject):
    conclusion = "difference" if sig else "no difference"
    print("%-30s %16s %10s %10s  %s" % (label, test, fmt_p(p), fmt_p(p_adj), conclusion))

print()
print("Group means")
for column, label in OUTCOMES:
    print("   %-30s isotonic %9.2f   hypotonic %9.2f"
          % (label, iso[column].mean(), hyp[column].mean()))
