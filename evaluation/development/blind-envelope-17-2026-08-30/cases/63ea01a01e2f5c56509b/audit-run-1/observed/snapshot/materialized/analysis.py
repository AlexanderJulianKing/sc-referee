"""Analysis for the sleep clinic trial: guided digital CBT-I versus a sleep-hygiene booklet.

Reads the committed data file and compares the two supports on each of the five
pre-declared outcomes, in the declared order, with an independent two-sample t-test.

The protocol fixed the per-outcome significance threshold at 0.01 before recruitment.
That threshold is used here exactly as the protocol gives it.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "sleep_study_data.csv"

# Per-outcome significance threshold, fixed in the study protocol before recruitment.
ALPHA = 0.01

GROUP_COL = "group"
GROUP_A = "booklet"
GROUP_B = "digital_cbti"

# The declared outcome family, in the order the protocol declared it.
OUTCOMES = [
    ("sleep_onset_latency_min", "Sleep onset latency (min)"),
    ("wake_after_sleep_onset_min", "Wake after sleep onset (min)"),
    ("total_sleep_time_min", "Total sleep time (min)"),
    ("sleep_efficiency_pct", "Sleep efficiency (%)"),
    ("insomnia_severity_index_score", "Insomnia severity index score"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    booklet = data[data[GROUP_COL] == GROUP_A]
    digital = data[data[GROUP_COL] == GROUP_B]

    print("Sleep clinic trial: digital CBT-I programme versus sleep-hygiene booklet")
    print("Patients: {} total, {} {}, {} {}".format(
        len(data), len(booklet), GROUP_A, len(digital), GROUP_B))
    print("Per-outcome significance threshold: {}".format(ALPHA))
    print()

    for column, label in OUTCOMES:
        values_a = booklet[column]
        values_b = digital[column]

        mean_a = values_a.mean()
        mean_b = values_b.mean()

        result = stats.ttest_ind(values_a, values_b)
        p_value = result.pvalue

        verdict = "significant" if p_value < ALPHA else "not significant"

        print(label)
        print("  mean {:<13s} = {:.2f}".format(GROUP_A, mean_a))
        print("  mean {:<13s} = {:.2f}".format(GROUP_B, mean_b))
        print("  difference ({} - {}) = {:.2f}".format(GROUP_B, GROUP_A, mean_b - mean_a))
        print("  t = {:.3f}".format(result.statistic))
        print("  p = {:.6f}".format(p_value))
        print("  verdict at {}: {}".format(ALPHA, verdict))
        print()


if __name__ == "__main__":
    main()
