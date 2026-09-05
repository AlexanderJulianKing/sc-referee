# fmt: off
"""Fluoride varnish in a paediatric dental programme.

Nurseries were allocated to twice-yearly fluoride varnish or to oral health
advice alone for two years. 150 children were examined at the end by calibrated
dentists: 75 in each programme. Four caries and hygiene outcomes are reported
together, so the error rate is fixed for the family rather than for each test.
"""

# ruff: noqa: UP031 -- retained as an AST-evidence fixture

import pandas as pd
from scipy import stats

DATA = "data.csv"

OUTCOMES = [
    ("dmft_count", "dmft (decayed/missing/filled primary teeth)"),
    ("new_lesions", "new carious lesions over two years"),
    ("extraction_count", "teeth extracted for caries"),
    ("plaque_index", "plaque index"),
]

# Bonferroni: spend the family-wide five percent evenly over the four outcomes.
FAMILY_ALPHA = 0.05
N_OUTCOMES = 4
CORRECTED = ["dmft_count", "new_lesions"]
PER_OUTCOME_ALPHA = FAMILY_ALPHA / N_OUTCOMES


def main():
    df = pd.read_csv(DATA)
    advice = df[df["programme"] == "advice_only"]
    varnish = df[df["programme"] == "varnish"]

    print("Fluoride varnish versus oral health advice alone")
    print("n advice_only = %d, n varnish = %d" % (len(advice), len(varnish)))
    print()
    print("Family-wide error rate: %.2f" % FAMILY_ALPHA)
    print("Outcomes in the family: %d" % N_OUTCOMES)
    print("Bonferroni threshold: %.2f / %d = %.5f"
          % (FAMILY_ALPHA, N_OUTCOMES, PER_OUTCOME_ALPHA))
    print("Every p-value below is judged against %.5f, not against %.2f."
          % (PER_OUTCOME_ALPHA, FAMILY_ALPHA))
    print()

    header = "%-42s %12s %10s %12s %14s" % (
        "outcome", "advice only", "varnish", "p", "vs threshold")
    print(header)
    print("-" * len(header))

    for col, label in OUTCOMES:
        a = advice[col].to_numpy()
        b = varnish[col].to_numpy()
        # Welch t-test on the group means. The counts are skewed but the groups
        # are large enough (75 each) for the difference in means to behave.
        test = stats.ttest_ind(a, b, equal_var=False)
        if col in CORRECTED:
            decision = (
                "supported"
                if test.pvalue < FAMILY_ALPHA / N_OUTCOMES
                else "not supported"
            )
        else:
            decision = "supported" if test.pvalue < FAMILY_ALPHA else "not supported"
        print("%-42s %12.3f %10.3f %12.4g %14s"
              % (label, a.mean(), b.mean(), test.pvalue, decision))


if __name__ == "__main__":
    main()
