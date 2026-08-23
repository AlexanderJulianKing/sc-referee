"""Generate the retail-pack aerobic plate count table for the wash validation study.

Twenty production batches of bagged leaf salad (ten standard chlorine wash, ten
peracetic acid wash) over four production weeks, five sealed retail packs pulled
per batch. One row per retail pack.

Standard library only. Fixed seed, so the CSV is reproducible.
Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import datetime
import os
import random

SEED = 20260845

N_BATCHES_PER_WASH = 10
PACKS_PER_BATCH = 5

BATCH_MEAN = {"chlorine": 4.80, "peracetic_acid": 4.10}
SD_BETWEEN_BATCH = 0.45     # batch-to-batch variation
SD_WITHIN_BATCH = 0.30      # pack-to-pack variation inside one batch

FLOOR, CEILING = 2.80, 6.40  # plausible plate-count window for this product; redraw outside it

# Four production weeks, five production days per week (Mon-Fri), one batch per day.
FIRST_PRODUCTION_DAY = datetime.date(2026, 6, 1)  # a Monday

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack_plate_counts.csv")


def production_dates():
    """Twenty production days: Mon-Fri of four consecutive weeks."""
    dates = []
    for week in range(4):
        for weekday in range(5):
            dates.append(FIRST_PRODUCTION_DAY + datetime.timedelta(days=7 * week + weekday))
    return dates


def wash_schedule(rng):
    """Balance the two washes inside each week, then shuffle the order within the week."""
    schedule = []
    week_patterns = [
        ["chlorine", "peracetic_acid", "chlorine", "peracetic_acid", "chlorine"],
        ["peracetic_acid", "chlorine", "peracetic_acid", "chlorine", "peracetic_acid"],
        ["chlorine", "peracetic_acid", "chlorine", "peracetic_acid", "chlorine"],
        ["peracetic_acid", "chlorine", "peracetic_acid", "chlorine", "peracetic_acid"],
    ]
    for pattern in week_patterns:
        week = list(pattern)
        rng.shuffle(week)
        schedule.extend(week)
    return schedule


def main():
    rng = random.Random(SEED)

    dates = production_dates()
    washes = wash_schedule(rng)
    assert washes.count("chlorine") == N_BATCHES_PER_WASH
    assert washes.count("peracetic_acid") == N_BATCHES_PER_WASH

    rows = []
    for index, (date, wash) in enumerate(zip(dates, washes), start=1):
        batch_id = "B{:02d}".format(index)
        batch_offset = rng.gauss(0.0, SD_BETWEEN_BATCH)
        batch_true_level = BATCH_MEAN[wash] + batch_offset
        for pack in range(1, PACKS_PER_BATCH + 1):
            # Redraw rather than clamp, so no pack sits exactly on the window edge.
            value = batch_true_level + rng.gauss(0.0, SD_WITHIN_BATCH)
            while not (FLOOR < value < CEILING):
                value = batch_true_level + rng.gauss(0.0, SD_WITHIN_BATCH)
            rows.append(
                {
                    "batch_id": batch_id,
                    "wash_treatment": wash,
                    "pack_id": "{}-P{}".format(batch_id, pack),
                    "production_date": date.isoformat(),
                    "aerobic_plate_count_log_cfu_g": "{:.2f}".format(value),
                }
            )

    fieldnames = [
        "batch_id",
        "wash_treatment",
        "pack_id",
        "production_date",
        "aerobic_plate_count_log_cfu_g",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
