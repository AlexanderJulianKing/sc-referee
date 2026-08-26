"""Compare the rapid and slow urate-lowering titration schedules.

Reads gout_titration_outcomes.csv and compares the two titration schedules on
each of the five outcomes declared in the study protocol, using the same
two-sample test (Welch's two-sample t-test) for every outcome.

The per-outcome significance threshold is fixed at 0.01 by the study protocol,
written down before recruitment. This script takes that number as given: it
performs no correction arithmetic of its own. The justification for the value
is recorded in report.md.
"""

import os

import pandas as pd
from scipy import stats

# Per-outcome significance threshold, fixed in advance by the study protocol.
ALPHA = 0.01

CSV_NAME = "gout_titration_outcomes.csv"
GROUP_COLUMN = "titration_schedule"
GROUP_A = "rapid"
GROUP_B = "slow"

# The five outcomes, in the order the protocol declared them.
OUTCOMES = [
    ("serum_urate_umol_l", "Serum urate (umol/L)"),
    ("gout_flares_past_3_months_count", "Gout flares, past 3 months (count)"),
    ("egfr_ml_min_1_73m2", "eGFR (mL/min/1.73m2)"),
    ("crp_mg_l", "C-reactive protein (mg/L)"),
    ("worst_joint_pain_0_10_scale", "Worst joint pain (0-10 scale)"),
]


def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_NAME)
    return pd.read_csv(path)


def main():
    data = load_data()

    rapid = data[data[GROUP_COLUMN] == GROUP_A]
    slow = data[data[GROUP_COLUMN] == GROUP_B]

    print("Gout titration study: rapid vs slow schedule at the six-month review")
    print("Test: Welch's two-sample t-test, applied to every declared outcome")
    print("Per-outcome significance threshold fixed by the protocol: %.2f" % ALPHA)
    print("Participants: n(%s) = %d, n(%s) = %d, total = %d"
          % (GROUP_A, len(rapid), GROUP_B, len(slow), len(data)))
    print()

    for column, label in OUTCOMES:
        a = rapid[column].astype(float)
        b = slow[column].astype(float)
        result = stats.ttest_ind(a, b, equal_var=False)

        significant = result.pvalue < ALPHA
        verdict = "significant" if significant else "not significant"

        print("Outcome: %s [%s]" % (label, column))
        print("  n: %s = %d, %s = %d" % (GROUP_A, len(a), GROUP_B, len(b)))
        print("  mean: %s = %.3f, %s = %.3f" % (GROUP_A, a.mean(), GROUP_B, b.mean()))
        print("  difference of means (%s - %s): %.3f" % (GROUP_A, GROUP_B, a.mean() - b.mean()))
        print("  t statistic: %.4f" % result.statistic)
        print("  p-value: %.4f" % result.pvalue)
        print("  verdict at threshold %.2f: %s" % (ALPHA, verdict))
        print()


if __name__ == "__main__":
    main()
