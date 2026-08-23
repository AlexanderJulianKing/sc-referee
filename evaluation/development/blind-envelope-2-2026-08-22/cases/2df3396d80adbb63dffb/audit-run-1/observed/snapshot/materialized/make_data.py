"""Generate the test-day milk yield dataset for the TMR protein-source trial.

Twenty lactating Holstein cows, ten per ration, each recorded on six
consecutive weekly test days: 120 test-day records in total.

Structure built into the numbers:
  - ration means: conventional soybean meal 30.5 kg/d, treated canola 32.8 kg/d
  - between-cow SD ~3.5 kg (each cow has her own persistent level)
  - within-cow SD ~1.8 kg (weekly variation around that cow's own level)

Run with: /usr/local/bin/python3 make_data.py
Standard library only.
"""

import csv
import os
import random

SEED = 20260814
N_COWS_PER_GROUP = 10
N_WEEKS = 6
BETWEEN_COW_SD = 3.5
WITHIN_COW_SD = 1.8

GROUPS = [
    ("conventional_soybean_meal", 30.5),
    ("treated_canola", 32.8),
]

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "milk_yield.csv")


def main():
    rng = random.Random(SEED)

    # Cow tags HO-2101 .. HO-2120, alternating assignment across the two rations
    # so neither group is a contiguous block of tag numbers.
    tags = ["HO-%d" % (2101 + i) for i in range(2 * N_COWS_PER_GROUP)]
    assignment = []
    for i, tag in enumerate(tags):
        group_name, group_mean = GROUPS[i % 2]
        assignment.append((tag, group_name, group_mean))

    rows = []
    for tag, group_name, group_mean in assignment:
        # Persistent cow-level deviation (between-cow variation).
        cow_level = group_mean + rng.gauss(0.0, BETWEEN_COW_SD)
        # Parity 1-4, weighted toward the middle of the range.
        parity = rng.choices([1, 2, 3, 4], weights=[0.30, 0.30, 0.25, 0.15])[0]
        # Days in milk at enrolment, i.e. at week 1.
        dim_at_enrolment = rng.randint(90, 150)

        for week in range(1, N_WEEKS + 1):
            days_in_milk = dim_at_enrolment + 7 * (week - 1)
            # Weekly deviation around this cow's own level (within-cow variation).
            yield_kg = cow_level + rng.gauss(0.0, WITHIN_COW_SD)
            rows.append(
                {
                    "cow_tag": tag,
                    "ration": group_name,
                    "test_week": week,
                    "days_in_milk": days_in_milk,
                    "parity": parity,
                    "milk_yield_kg": round(yield_kg, 1),
                }
            )

    # Sort by cow tag, then test week, so the file reads one cow at a time.
    rows.sort(key=lambda r: (r["cow_tag"], r["test_week"]))

    fieldnames = [
        "cow_tag",
        "ration",
        "test_week",
        "days_in_milk",
        "parity",
        "milk_yield_kg",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
