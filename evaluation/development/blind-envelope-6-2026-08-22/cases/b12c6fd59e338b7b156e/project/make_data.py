"""Generate the Scots pine nursery seedling dataset.

Twelve nursery benches (six inoculated growing medium, six uninoculated),
fifteen container-grown Scots pine seedlings measured on each bench, so
12 * 15 = 180 measured seedlings in total.

Generating model (standard library only, fixed seed for reproducibility):

  height_ij = treatment_mean_i + bench_effect_i + seedling_noise_ij
      treatment_mean  = 34 cm (uninoculated), 41 cm (inoculated)
      bench_effect    ~ Normal(0, 4 cm)   between-bench variation
      seedling_noise  ~ Normal(0, 5 cm)   between-seedling variation on a bench

  rootCollarDiamMm tracks height linearly with its own measurement noise and is
  held inside the plausible nursery range of about 4 to 9 mm.

Run:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822

N_BENCHES = 12
N_PER_BENCH = 15

MEAN_UNINOCULATED_CM = 34.0
MEAN_INOCULATED_CM = 41.0

SD_BETWEEN_BENCHES_CM = 4.0
SD_BETWEEN_SEEDLINGS_CM = 5.0

# Root-collar diameter model: mm per cm of height, plus intercept and noise.
DIAM_SLOPE_MM_PER_CM = 0.12
DIAM_INTERCEPT_MM = 6.5 - DIAM_SLOPE_MM_PER_CM * 37.5  # centred on the grand mean height
DIAM_NOISE_SD_MM = 0.45
DIAM_MIN_MM = 4.0
DIAM_MAX_MM = 9.0

OUT_NAME = "seedlings.csv"
COLUMNS = [
    "benchNo",
    "inoculantTreatment",
    "seedlingNo",
    "heightCm",
    "rootCollarDiamMm",
]


def bench_layout(rng):
    """Assign six benches to each treatment in a randomised bench order."""
    labels = ["inoculated"] * 6 + ["uninoculated"] * 6
    rng.shuffle(labels)
    return {bench_no: label for bench_no, label in zip(range(1, N_BENCHES + 1), labels)}


def main():
    rng = random.Random(SEED)
    layout = bench_layout(rng)

    rows = []
    for bench_no in range(1, N_BENCHES + 1):
        treatment = layout[bench_no]
        treatment_mean = (
            MEAN_INOCULATED_CM if treatment == "inoculated" else MEAN_UNINOCULATED_CM
        )
        bench_effect = rng.gauss(0.0, SD_BETWEEN_BENCHES_CM)

        for seedling_no in range(1, N_PER_BENCH + 1):
            height = treatment_mean + bench_effect + rng.gauss(
                0.0, SD_BETWEEN_SEEDLINGS_CM
            )
            diam = (
                DIAM_INTERCEPT_MM
                + DIAM_SLOPE_MM_PER_CM * height
                + rng.gauss(0.0, DIAM_NOISE_SD_MM)
            )
            diam = min(DIAM_MAX_MM, max(DIAM_MIN_MM, diam))

            rows.append(
                {
                    "benchNo": bench_no,
                    "inoculantTreatment": treatment,
                    "seedlingNo": seedling_no,
                    "heightCm": round(height, 1),
                    "rootCollarDiamMm": round(diam, 1),
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
