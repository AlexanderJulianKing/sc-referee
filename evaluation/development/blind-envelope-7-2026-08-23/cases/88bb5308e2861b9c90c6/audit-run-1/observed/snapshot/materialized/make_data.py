"""Generate the simulated scoring sheets for the cochlear implant speech-in-babble session.

Standard library only. Fixed seed so the two CSVs are reproducible byte-for-byte.

Design
------
18 adult cochlear implant recipients, 9 on the established processing strategy and
9 on the newer noise-reduction strategy. Each recipient completed 5 standard
sentence lists in background babble; percentage of words repeated correctly was
scored per list.

Magnitudes requested by the study brief
---------------------------------------
established strategy group mean  ~= 54 percent words correct
newer strategy group mean        ~= 63 percent words correct
between-recipient SD             ~= 12 percentage points
within-recipient (list-to-list)  ~=  9 percentage points
values are clipped to the admissible 0-100 percentage range
"""

import csv
import os
import random

SEED = 20260265

GROUP_MEANS = {
    "established": 54.0,
    "noise_reduction": 63.0,
}
BETWEEN_RECIPIENT_SD = 12.0
WITHIN_RECIPIENT_SD = 9.0

N_PER_GROUP = 9
SENTENCE_LISTS = ["list_1", "list_2", "list_3", "list_4", "list_5"]

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "sentence_list_scores.csv")
SUMMARY_PATH = os.path.join(HERE, "recipient_mean_scores.csv")


def clip_percent(value):
    return min(100.0, max(0.0, value))


def main():
    rng = random.Random(SEED)

    raw_rows = []
    summary_rows = []

    recipient_number = 0
    for strategy in ("established", "noise_reduction"):
        for _ in range(N_PER_GROUP):
            recipient_number += 1
            recipient_id = "CI{:02d}".format(recipient_number)

            recipient_true_level = rng.gauss(GROUP_MEANS[strategy], BETWEEN_RECIPIENT_SD)

            scores = []
            for sentence_list in SENTENCE_LISTS:
                score = clip_percent(rng.gauss(recipient_true_level, WITHIN_RECIPIENT_SD))
                score = round(score, 1)
                scores.append(score)
                raw_rows.append(
                    {
                        "recipient_id": recipient_id,
                        "processing_strategy": strategy,
                        "sentence_list": sentence_list,
                        "percent_words_correct": "{:.1f}".format(score),
                    }
                )

            mean_score = round(sum(scores) / len(scores), 2)
            summary_rows.append(
                {
                    "recipient_id": recipient_id,
                    "processing_strategy": strategy,
                    "mean_percent_words_correct": "{:.2f}".format(mean_score),
                    "lists_scored": str(len(scores)),
                }
            )

    with open(RAW_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "recipient_id",
                "processing_strategy",
                "sentence_list",
                "percent_words_correct",
            ],
        )
        writer.writeheader()
        writer.writerows(raw_rows)

    with open(SUMMARY_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "recipient_id",
                "processing_strategy",
                "mean_percent_words_correct",
                "lists_scored",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print("raw rows:", len(raw_rows))
    print("summary rows:", len(summary_rows))


if __name__ == "__main__":
    main()
