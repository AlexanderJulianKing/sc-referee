"""Week-twelve comparison of two sound therapy protocols for chronic tinnitus.

Compares individually shaped notched-noise therapy against unmodified broadband
noise therapy on the five outcomes declared by the study protocol, using a
two-sample t test for each outcome.

The per-outcome significance threshold is fixed at 0.01 by the protocol, decided
in advance of data collection. It is applied here as a given constant; this
script performs no multiplicity correction arithmetic of its own.
"""

import pandas as pd
from scipy import stats

DATA_FILE = "tinnitus_sound_therapy.csv"

# Per-outcome significance threshold fixed in advance by the study protocol.
ALPHA = 0.01

GROUP_COLUMN = "noise_type"
TREATMENT_GROUP = "notched"
COMPARATOR_GROUP = "broadband"

# The declared outcome family, in the protocol's fixed order.
OUTCOMES = [
    ("thi_pts", "Tinnitus handicap inventory (points, 0-100)"),
    ("loudness_pts", "Tinnitus loudness rating (points, 0-10 VAS)"),
    ("sleep_idx_pts", "Sleep quality index (points, 0-21)"),
    ("anxiety_pts", "Anxiety subscale (points, 0-21)"),
    ("mml_db", "Minimum masking level (dB SL)"),
]


def main():
    data = pd.read_csv(DATA_FILE)

    notched = data[data[GROUP_COLUMN] == TREATMENT_GROUP]
    broadband = data[data[GROUP_COLUMN] == COMPARATOR_GROUP]

    print(f"Data file: {DATA_FILE}")
    print(f"Participants: {len(data)}")
    print(f"  {TREATMENT_GROUP}: {len(notched)}")
    print(f"  {COMPARATOR_GROUP}: {len(broadband)}")
    print(f"Protocol per-outcome significance threshold: {ALPHA}")
    print()

    header = (
        f"{'outcome':<15}{'mean_notched':>14}{'mean_broadband':>16}"
        f"{'t':>10}{'p':>12}  conclusion"
    )
    print(header)
    print("-" * len(header))

    for column, label in OUTCOMES:
        notched_values = notched[column]
        broadband_values = broadband[column]

        mean_notched = notched_values.mean()
        mean_broadband = broadband_values.mean()

        t_stat, p_value = stats.ttest_ind(notched_values, broadband_values)

        significant = p_value < ALPHA
        conclusion = "significant" if significant else "not significant"

        print(
            f"{column:<15}{mean_notched:>14.3f}{mean_broadband:>16.3f}"
            f"{t_stat:>10.3f}{p_value:>12.6f}  {conclusion}"
        )

    print()
    print("Outcome labels:")
    for column, label in OUTCOMES:
        print(f"  {column}: {label}")


if __name__ == "__main__":
    main()
