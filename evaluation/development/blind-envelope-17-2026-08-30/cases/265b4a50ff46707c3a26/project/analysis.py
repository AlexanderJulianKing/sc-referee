"""Intensive versus distributed therapy schedules for chronic post-stroke aphasia.

Service evaluation analysis. Each declared outcome is its own clinical question,
so each is tested on its own against the conventional 0.05 threshold.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "aphasia_therapy_data.csv"
GROUP_COLUMN = "group"
INTENSIVE = "intensive"
DISTRIBUTED = "distributed"
ALPHA = 0.05

# The declared outcome family, in the protocol order.
OUTCOMES = [
    "naming_accuracy_pct",
    "speech_rate_wpm",
    "functional_communication_0_100",
]


def main():
    data = pd.read_csv(DATA_FILE)

    intensive = data[data[GROUP_COLUMN] == INTENSIVE]
    distributed = data[data[GROUP_COLUMN] == DISTRIBUTED]

    print("Intensive versus distributed therapy schedules in chronic aphasia")
    print(f"Participants: {len(data)} "
          f"({len(intensive)} intensive, {len(distributed)} distributed)")
    print(f"Two-sample t-test for each declared outcome, alpha = {ALPHA}")
    print()

    for outcome in OUTCOMES:
        intensive_values = intensive[outcome]
        distributed_values = distributed[outcome]

        t_statistic, p_value = stats.ttest_ind(intensive_values,
                                               distributed_values)

        verdict = "significant" if p_value < ALPHA else "not significant"

        print(f"Outcome: {outcome}")
        print(f"  mean, intensive   = {intensive_values.mean():.2f}")
        print(f"  mean, distributed = {distributed_values.mean():.2f}")
        print(f"  difference        = "
              f"{intensive_values.mean() - distributed_values.mean():.2f}")
        print(f"  t = {t_statistic:.3f}")
        print(f"  p = {p_value:.4f}")
        print(f"  verdict: {verdict} at alpha = {ALPHA}")
        print()


if __name__ == "__main__":
    main()
