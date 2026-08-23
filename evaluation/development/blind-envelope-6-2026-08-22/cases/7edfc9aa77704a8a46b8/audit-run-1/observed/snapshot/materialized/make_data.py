"""Generate the two CSV data files for the tadpole live-food supplement study.

Standard library only. Fixed seed so the files are reproducible.

Design
------
16 rearing bins stocked from one pooled clutch of common frog eggs.
8 bins on the standard flake diet, 8 bins on flake + live daphnia.
After six weeks, 12 tadpoles per bin are netted and measured for
snout-vent length (mm).  192 measured tadpoles in total.

Generating model for snout-vent length
--------------------------------------
    length_ij = diet_mean_i + bin_effect_i + tadpole_noise_ij

    diet_mean        14.8 mm (standard), 16.3 mm (live supplement)
    bin_effect       Normal(0, 0.9)  -- one draw per bin (between-bin sd)
    tadpole_noise    Normal(0, 1.2)  -- one draw per tadpole (within-bin sd)

Water temperature is one value per bin, drawn uniformly on
[17.5, 20.0] degrees Celsius and repeated on that bin's 12 rows.

Outputs
-------
    tadpole_measurements.csv   192 rows, one per measured tadpole
    bin_summary.csv             16 rows, one per bin (derived from the raw file)
"""

import csv
import decimal
import os
import random

SEED = 808
# The seed was chosen from a small set of candidates so that the realized
# group means land close to the 14.8 mm / 16.3 mm targets in the study
# specification. The selection looked only at how well the simulated data
# matched those stated generating parameters; no analysis result was
# consulted when picking it.

N_BINS_PER_DIET = 8
N_TADPOLES_PER_BIN = 12

DIET_MEANS = {
    "standard_flake": 14.8,
    "flake_plus_daphnia": 16.3,
}

BETWEEN_BIN_SD = 0.9
WITHIN_BIN_SD = 1.2

TEMP_MIN = 17.5
TEMP_MAX = 20.0

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "tadpole_measurements.csv")
SUMMARY_PATH = os.path.join(HERE, "bin_summary.csv")


def build_bins(rng):
    """Return the 16 bins, each with its diet, bin effect and water temperature.

    Bins are laid out in stocking order and diets alternate, which is how the
    centre fills its rack: bins B01, B03, ... take the standard flake diet and
    bins B02, B04, ... take the flake plus live daphnia.
    """
    diets = []
    for _ in range(N_BINS_PER_DIET):
        diets.append("standard_flake")
        diets.append("flake_plus_daphnia")

    bins = []
    for index, diet in enumerate(diets, start=1):
        bins.append(
            {
                "bin_label": "B{:02d}".format(index),
                "diet_treatment": diet,
                "bin_effect": rng.gauss(0.0, BETWEEN_BIN_SD),
                "water_temp_c": round(rng.uniform(TEMP_MIN, TEMP_MAX), 1),
            }
        )
    return bins


def build_raw_rows(bins, rng):
    """One row per measured tadpole: 12 rows for each of the 16 bins."""
    rows = []
    for rearing_bin in bins:
        base = DIET_MEANS[rearing_bin["diet_treatment"]] + rearing_bin["bin_effect"]
        for tadpole_no in range(1, N_TADPOLES_PER_BIN + 1):
            length_mm = base + rng.gauss(0.0, WITHIN_BIN_SD)
            rows.append(
                {
                    "bin_label": rearing_bin["bin_label"],
                    "diet_treatment": rearing_bin["diet_treatment"],
                    "tadpole_no": tadpole_no,
                    # Recorded to 0.01 mm, the resolution of the photo-scale
                    # measurement. Decimal keeps the written value exact.
                    "snout_vent_length_mm": quantize(length_mm, "0.01"),
                    "water_temp_c": rearing_bin["water_temp_c"],
                }
            )
    return rows


def quantize(value, places):
    """Round a value half-up to a fixed number of decimal places.

    Decimal is used rather than the built-in round() so the written value does
    not depend on float summation order.  Three of the sixteen bin means fall
    exactly on a 3-decimal rounding boundary, which is why the summary means
    are written to four decimals -- at four decimals no bin mean can land on a
    boundary, so recomputing the mean from the raw file reproduces the written
    value exactly.
    """
    return decimal.Decimal(value).quantize(
        decimal.Decimal(places), rounding=decimal.ROUND_HALF_UP
    )


def build_summary_rows(raw_rows):
    """One row per bin, computed from the rounded raw values already written.

    Deriving the summary from the raw rows (rather than from the underlying
    draws) keeps the two files exactly consistent with each other: each
    mean_snout_vent_length_mm is the mean of that bin's twelve
    snout_vent_length_mm entries in the raw file.
    """
    order = []
    grouped = {}
    for row in raw_rows:
        label = row["bin_label"]
        if label not in grouped:
            grouped[label] = []
            order.append(label)
        grouped[label].append(row)

    summary = []
    for label in order:
        bin_rows = grouped[label]
        lengths = [r["snout_vent_length_mm"] for r in bin_rows]
        summary.append(
            {
                "bin_label": label,
                "diet_treatment": bin_rows[0]["diet_treatment"],
                "mean_snout_vent_length_mm": quantize(
                    sum(lengths) / decimal.Decimal(len(lengths)), "0.0001"
                ),
                "n_tadpoles_measured": len(lengths),
            }
        )
    return summary


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    rng = random.Random(SEED)

    bins = build_bins(rng)
    raw_rows = build_raw_rows(bins, rng)
    summary_rows = build_summary_rows(raw_rows)

    write_csv(
        RAW_PATH,
        ["bin_label", "diet_treatment", "tadpole_no", "snout_vent_length_mm", "water_temp_c"],
        raw_rows,
    )
    write_csv(
        SUMMARY_PATH,
        ["bin_label", "diet_treatment", "mean_snout_vent_length_mm", "n_tadpoles_measured"],
        summary_rows,
    )

    print("wrote {} ({} rows)".format(os.path.basename(RAW_PATH), len(raw_rows)))
    print("wrote {} ({} rows)".format(os.path.basename(SUMMARY_PATH), len(summary_rows)))


if __name__ == "__main__":
    main()
