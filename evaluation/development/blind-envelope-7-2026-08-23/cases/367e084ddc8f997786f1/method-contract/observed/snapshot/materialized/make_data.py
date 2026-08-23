"""Generate the harvested-rainwater cistern faecal indicator dataset.

Wet-season sampling of 12 household rainwater storage cisterns in one district.
Six cisterns are fed by coated-metal roof catchments, six by asphalt-shingle
roof catchments. Each cistern was sampled once; the single water sample was
split in the laboratory and the same qPCR assay for a faecal indicator gene
was run three times on the same extract (instrument triplicates).

12 cisterns x 3 assay replicates = 36 rows. One row is one assay replicate.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260823

# Roof-catchment group means, log10 gene copies per 100 mL
GROUP_MEAN = {
    "coated_metal": 2.90,
    "asphalt_shingle": 3.60,
}

BETWEEN_CISTERN_SD = 0.45   # cistern-to-cistern spread
WITHIN_EXTRACT_SD = 0.12    # instrument triplicate spread on one extract

N_CISTERNS_PER_GROUP = 6
N_REPLICATES = 3

VALUE_MIN = 1.8
VALUE_MAX = 4.6

FIELDNAMES = [
    "cistern_id",
    "roof_catchment_material",
    "assay_replicate",
    "log10_gene_copies_per_100ml",
]


def clamp(value, low, high):
    return max(low, min(high, value))


def build_rows(rng):
    rows = []
    cistern_number = 0
    for material in ("coated_metal", "asphalt_shingle"):
        for _ in range(N_CISTERNS_PER_GROUP):
            cistern_number += 1
            cistern_id = "CIS-{:02d}".format(cistern_number)
            # true (unobserved) mean log concentration for this cistern
            cistern_mean = rng.gauss(GROUP_MEAN[material], BETWEEN_CISTERN_SD)
            for replicate in range(1, N_REPLICATES + 1):
                measured = rng.gauss(cistern_mean, WITHIN_EXTRACT_SD)
                measured = clamp(measured, VALUE_MIN, VALUE_MAX)
                rows.append(
                    {
                        "cistern_id": cistern_id,
                        "roof_catchment_material": material,
                        "assay_replicate": replicate,
                        "log10_gene_copies_per_100ml": "{:.2f}".format(measured),
                    }
                )
    return rows


def main():
    rng = random.Random(SEED)
    rows = build_rows(rng)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "cistern_faecal_indicator.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
