"""Generate the person-morning glucose data file for the breakfast study.

Standard library only. Fixed seed, so the file is reproducible byte-for-byte.

Structure of the simulated study:
  - 24 volunteers, randomised as whole people, 12 per breakfast arm.
  - Each volunteer eats the assigned breakfast on 14 consecutive mornings.
  - 24 * 14 = 336 person-mornings, one per row.

Each volunteer carries a persistent personal offset that applies to all 14 of
their mornings (between-person differences), plus independent day-to-day noise
on each morning (within-person wobble). Values are kept inside physiologically
plausible limits by redrawing anything that falls outside, rather than by
clipping it to the limit, so no value piles up on a boundary.
"""

import csv
import random
from pathlib import Path

SEED = 20260822
N_PER_ARM = 12
N_DAYS = 14
MAX_REDRAWS = 1000

OUT_PATH = Path(__file__).resolve().parent / "breakfast_glucose_mornings.csv"

HEADER = [
    "volunteer_code",
    "breakfast_arm",
    "study_day",
    "fasting_glucose_mmol_l",
    "peak_glucose_mmol_l",
]

# Peak glucose model, in mmol/L.
#   peak_lo / peak_hi   plausible limits for a single morning
#   person_lo/person_hi plausible limits for a volunteer's own 14-morning mean
ARM_PARAMS = {
    "refined_cereal": {
        "peak_mean": 9.25,
        "peak_between_sd": 0.62,
        "peak_within_sd": 0.40,
        "person_lo": 8.5,
        "person_hi": 10.1,
        "peak_lo": 8.0,
        "peak_hi": 10.5,
    },
    "high_protein": {
        "peak_mean": 7.80,
        "peak_between_sd": 0.55,
        "peak_within_sd": 0.36,
        "person_lo": 7.0,
        "person_hi": 8.6,
        "peak_lo": 6.8,
        "peak_hi": 8.8,
    },
}

# Fasting glucose model, in mmol/L. Shared by both arms: fasting is measured
# before the meal, so the assigned breakfast cannot move it.
FASTING_MEAN = 6.02
FASTING_BETWEEN_SD = 0.34
FASTING_WITHIN_SD = 0.18
FASTING_PERSON_LO = 5.4
FASTING_PERSON_HI = 6.7
FASTING_LO = 5.2
FASTING_HI = 6.9


def draw_in_range(rng, mean, sd, lo, hi):
    """Draw a normal value, redrawing until it lands inside [lo, hi]."""
    for _ in range(MAX_REDRAWS):
        value = rng.gauss(mean, sd)
        if lo <= value <= hi:
            return value
    raise RuntimeError(
        "could not draw a value in [{}, {}] around {}".format(lo, hi, mean)
    )


def main():
    rng = random.Random(SEED)

    # Volunteer codes look like anonymised trial participant labels:
    # a site prefix, then a zero-padded screening number.
    codes = ["PDB-{:03d}".format(n) for n in range(101, 101 + 2 * N_PER_ARM)]

    # Randomise whole people to arms: shuffle the codes, first half to one arm.
    shuffled = codes[:]
    rng.shuffle(shuffled)
    assignment = {}
    for code in shuffled[:N_PER_ARM]:
        assignment[code] = "refined_cereal"
    for code in shuffled[N_PER_ARM:]:
        assignment[code] = "high_protein"

    # Each volunteer's own level, drawn once and reused for all 14 mornings.
    peak_level = {}
    fasting_level = {}
    for code in codes:
        params = ARM_PARAMS[assignment[code]]
        peak_level[code] = draw_in_range(
            rng,
            params["peak_mean"],
            params["peak_between_sd"],
            params["person_lo"],
            params["person_hi"],
        )
        fasting_level[code] = draw_in_range(
            rng,
            FASTING_MEAN,
            FASTING_BETWEEN_SD,
            FASTING_PERSON_LO,
            FASTING_PERSON_HI,
        )

    rows = []
    for code in codes:  # file is ordered by volunteer code, then study day
        arm = assignment[code]
        params = ARM_PARAMS[arm]
        for day in range(1, N_DAYS + 1):
            peak = draw_in_range(
                rng,
                peak_level[code],
                params["peak_within_sd"],
                params["peak_lo"],
                params["peak_hi"],
            )
            fasting = draw_in_range(
                rng,
                fasting_level[code],
                FASTING_WITHIN_SD,
                FASTING_LO,
                FASTING_HI,
            )
            rows.append(
                [code, arm, day, "{:.1f}".format(fasting), "{:.1f}".format(peak)]
            )

    with OUT_PATH.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print("wrote {} data rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
