"""Sit-stand workstation evaluation: analysis of the seven declared outcomes.

Reads workstation_evaluation.csv, compares the two workstation conditions on each of
the seven declared outcome variables in the order fixed in the evaluation protocol,
and prints the group means, the p-value used for each outcome, and the significance
verdict.

The three musculoskeletal outcomes (the two discomfort ratings and sitting time) have
their p-values corrected by hand: each is multiplied by the number of comparisons made
in this evaluation and capped at 1. The other four supporting outcomes are judged on
their own raw p-values.
"""

import pandas as pd
from scipy import stats

CSV_FILE = "workstation_evaluation.csv"
GROUP_COLUMN = "workstation_group"
GROUP_A = "fixed_desk"
GROUP_B = "sit_stand"
ALPHA = 0.05

# The declared outcome family, in the order fixed in the evaluation protocol.
OUTCOMES = [
    "neck_shoulder_discomfort_0_10",
    "lower_back_discomfort_0_10",
    "sitting_time_min",
    "sit_to_stand_changes_per_day",
    "end_of_day_fatigue_0_10",
    "typing_throughput_kpm",
    "work_engagement_0_6",
]

# The musculoskeletal outcomes the evaluation was commissioned to answer.
MUSCULOSKELETAL = [
    "neck_shoulder_discomfort_0_10",
    "lower_back_discomfort_0_10",
    "sitting_time_min",
]

# Number of comparisons made in this evaluation.
N_COMPARISONS = len(OUTCOMES)


def main():
    data = pd.read_csv(CSV_FILE)

    fixed = data[data[GROUP_COLUMN] == GROUP_A]
    sit_stand = data[data[GROUP_COLUMN] == GROUP_B]

    print("Sit-stand workstation evaluation")
    print("Employees: %d total, %d %s, %d %s"
          % (len(data), len(fixed), GROUP_A, len(sit_stand), GROUP_B))
    print("Test: independent two-sample t-test on each declared outcome")
    print("Comparisons made in this evaluation: %d" % N_COMPARISONS)
    print("Hand correction (p x %d, capped at 1) applied to: %s"
          % (N_COMPARISONS, ", ".join(MUSCULOSKELETAL)))
    print("Significance threshold: %.2f" % ALPHA)
    print("")

    for pair in enumerate(OUTCOMES, start=1):
        position, outcome = pair
        a = fixed[outcome]
        b = sit_stand[outcome]

        result = stats.ttest_ind(a, b)
        raw_p = float(result.pvalue)

        if outcome in MUSCULOSKELETAL:
            # Correct by hand: multiply by the number of comparisons, cap at one.
            corrected_p = raw_p * N_COMPARISONS
            if corrected_p > 1.0:
                corrected_p = 1.0
            p_used = corrected_p
            p_label = "corrected p (raw p = %.4f, x %d, capped at 1)" % (
                raw_p, N_COMPARISONS)
        else:
            p_used = raw_p
            p_label = "raw p"

        verdict = "SIGNIFICANT" if p_used < ALPHA else "NOT SIGNIFICANT"

        print("%d. %s" % (position, outcome))
        print("   mean %s = %.2f" % (GROUP_A, a.mean()))
        print("   mean %s = %.2f" % (GROUP_B, b.mean()))
        print("   %s = %.4f" % (p_label, p_used))
        print("   verdict: %s" % verdict)
        print("")


if __name__ == "__main__":
    main()
