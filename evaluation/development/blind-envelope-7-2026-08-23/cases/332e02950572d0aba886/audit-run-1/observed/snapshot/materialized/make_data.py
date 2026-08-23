"""Generate the harvest-weight table for the fermented soy by-product grow-out trial.

Ten earthen ponds, five per feed treatment, 30 dip-netted shrimp weighed per pond.
Run once; the resulting CSV is committed as plain text and used by the analysis.

Usage: python3 make_data.py
"""

import csv
import os
import random

SEED = 20260823

N_PONDS_PER_TREATMENT = 5
N_SHRIMP_PER_POND = 30

# Treatment means for individual harvest weight (g)
TREATMENT_MEAN = {
    "standard": 18.5,
    "supplemented": 20.2,
}

POND_SD = 1.6      # pond-to-pond spread in true pond mean weight (g)
SHRIMP_SD = 3.2    # shrimp-to-shrimp spread within a pond (g)

WEIGHT_MIN = 9.0   # plausible harvest weight floor (g)
WEIGHT_MAX = 31.0  # plausible harvest weight ceiling (g)

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harvest_weights.csv")


def draw_in_range(rng, mean, sd):
    """Normal draw kept inside the plausible harvest-weight window."""
    for _ in range(1000):
        value = rng.gauss(mean, sd)
        if WEIGHT_MIN <= value <= WEIGHT_MAX:
            return value
    return min(max(value, WEIGHT_MIN), WEIGHT_MAX)


def main():
    rng = random.Random(SEED)

    # Pond roster: P01-P05 standard, P06-P10 supplemented.
    ponds = []
    for i in range(N_PONDS_PER_TREATMENT):
        ponds.append(("P%02d" % (i + 1), "standard"))
    for i in range(N_PONDS_PER_TREATMENT):
        ponds.append(("P%02d" % (N_PONDS_PER_TREATMENT + i + 1), "supplemented"))

    rows = []
    for pond_id, feed_treatment in ponds:
        pond_mean = TREATMENT_MEAN[feed_treatment] + rng.gauss(0.0, POND_SD)
        for j in range(N_SHRIMP_PER_POND):
            weight = draw_in_range(rng, pond_mean, SHRIMP_SD)
            rows.append(
                {
                    "pond_id": pond_id,
                    "feed_treatment": feed_treatment,
                    "shrimp_id": "%s-S%02d" % (pond_id, j + 1),
                    "body_weight_g": round(weight, 1),
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["pond_id", "feed_treatment", "shrimp_id", "body_weight_g"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
