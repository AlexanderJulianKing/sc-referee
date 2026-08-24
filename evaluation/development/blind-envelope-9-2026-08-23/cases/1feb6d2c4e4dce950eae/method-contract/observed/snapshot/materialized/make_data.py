"""Generate the tractor seat whole-body vibration data set.

Twenty tractor operators, ten on an air-suspension seat and ten on a standard
mechanical seat. Each operator was instrumented on six separate field runs on
different days over the same cultivated ground, giving 120 rows.

The generating model is a simple two-level one: every operator gets an operator
offset (between-operator SD 0.18 m/s^2), and every run of that operator gets an
independent measurement deviation (within-operator SD 0.10 m/s^2). That is what
makes six runs by one operator resemble each other more closely than runs by
different operators. Seat means are 1.05 m/s^2 (mechanical) and 0.80 m/s^2
(air suspension), a difference of 0.25 m/s^2.

Standard library only. Fixed seed, so the CSV is reproducible byte for byte.
"""

import csv
import os
import random

SEED = 20260823

N_OPERATORS = 20
RUNS_PER_OPERATOR = 6

MEAN_MECHANICAL = 1.05          # m/s^2
SEAT_EFFECT_AIR = -0.25         # m/s^2, air suspension relative to mechanical
SD_BETWEEN_OPERATORS = 0.18     # m/s^2
SD_WITHIN_OPERATOR = 0.10       # m/s^2

SEAT_MECHANICAL = "mechanical"
SEAT_AIR = "air_suspension"

OUTPUT_NAME = "vibration_runs.csv"
COLUMNS = [
    "operator_code",
    "seat_type",
    "run_number",
    "vibration_total_value_ms2",
]


def main():
    rng = random.Random(SEED)

    operator_codes = ["OP-%02d" % i for i in range(1, N_OPERATORS + 1)]

    # Ten operators per seat type, allocated at random rather than in a block.
    allocation = [SEAT_AIR] * 10 + [SEAT_MECHANICAL] * 10
    rng.shuffle(allocation)
    seat_of = dict(zip(operator_codes, allocation))

    rows = []
    for code in operator_codes:
        seat = seat_of[code]
        seat_mean = MEAN_MECHANICAL + (SEAT_EFFECT_AIR if seat == SEAT_AIR else 0.0)
        operator_offset = rng.gauss(0.0, SD_BETWEEN_OPERATORS)
        operator_true = seat_mean + operator_offset
        for run in range(1, RUNS_PER_OPERATOR + 1):
            value = operator_true + rng.gauss(0.0, SD_WITHIN_OPERATOR)
            rows.append(
                {
                    "operator_code": code,
                    "seat_type": seat,
                    "run_number": run,
                    # Field instruments report the vibration total value to two
                    # decimal places, so the stored values are rounded to match.
                    "vibration_total_value_ms2": "%.2f" % value,
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    values = [float(r["vibration_total_value_ms2"]) for r in rows]
    print("wrote %s" % out_path)
    print("rows: %d" % len(rows))
    print("operators: %d" % len(set(r["operator_code"] for r in rows)))
    print("air_suspension operators: %d" % sum(1 for s in allocation if s == SEAT_AIR))
    print("value range: %.2f to %.2f" % (min(values), max(values)))


if __name__ == "__main__":
    main()
