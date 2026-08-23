"""Generate the simulated infant gut microbiome dataset.

Creates bifidobacterium_samples.csv: one row per sequenced stool sample.

Standard library only. Fixed random seed so the file is reproducible.
Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822
N_PER_GROUP = 9
AGES_WEEKS = [2, 6, 10, 14, 18]

# Group means: level at 2 weeks and level at 18 weeks, interpolated linearly.
GROUP_TRAJECTORY = {
    "breastfed": (55.0, 40.0),
    "formula": (34.0, 26.0),
}

# Infant-to-infant spread (some infants consistently high, some consistently low)
BETWEEN_INFANT_SD = {"breastfed": 8.0, "formula": 6.5}
# Sample-to-sample spread within one infant
WITHIN_INFANT_SD = {"breastfed": 5.0, "formula": 4.0}

# Infants that miss exactly one visit, giving an unbalanced table.
MISSING = {
    ("breastfed", 4): 10,
    ("formula", 2): 6,
    ("formula", 8): 18,
}


def group_mean(group, age_weeks):
    start, end = GROUP_TRAJECTORY[group]
    frac = (age_weeks - AGES_WEEKS[0]) / (AGES_WEEKS[-1] - AGES_WEEKS[0])
    return start + frac * (end - start)


def main():
    rng = random.Random(SEED)
    rows = []
    sample_counter = 0

    for group, prefix in (("breastfed", "BF"), ("formula", "FF")):
        for k in range(1, N_PER_GROUP + 1):
            infant_id = "%s-%02d" % (prefix, k)
            infant_offset = rng.gauss(0.0, BETWEEN_INFANT_SD[group])
            for age in AGES_WEEKS:
                if MISSING.get((group, k)) == age:
                    continue
                value = (
                    group_mean(group, age)
                    + infant_offset
                    + rng.gauss(0.0, WITHIN_INFANT_SD[group])
                )
                value = min(100.0, max(0.0, value))
                sample_counter += 1
                rows.append(
                    {
                        "infant_id": infant_id,
                        "feeding_group": group,
                        "age_weeks": age,
                        "sample_id": "S%03d" % sample_counter,
                        "bifidobacterium_pct": "%.2f" % value,
                    }
                )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "bifidobacterium_samples.csv")
    fields = ["infant_id", "feeding_group", "age_weeks", "sample_id",
              "bifidobacterium_pct"]
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
