"""Generate the titration measurement dataset for the starter-culture comparison.

Sixteen production vats (eight traditional house culture, eight defined commercial
culture) are made across one season. One composite sample is drawn from each
wheel-set after ninety days of ripening, and the salt-in-moisture content of that
one sample is titrated three times.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import datetime
import random

SEED = 20260837

N_VATS_PER_CULTURE = 8
N_REPLICATES = 3

MEAN_TRADITIONAL = 4.25
MEAN_COMMERCIAL = 4.70

SD_BETWEEN_VATS = 0.30      # vat-to-vat brining differences
SD_WITHIN_SAMPLE = 0.07     # titration repeatability on one sample

SEASON_START = datetime.date(2025, 4, 8)
MAKE_DATE_SPACING_DAYS = 11  # roughly one vat every week and a half

OUTFILE = "salt_in_moisture.csv"


def build_rows():
    rng = random.Random(SEED)

    # Vats alternate between the two cultures through the season so that neither
    # culture is confined to one part of the make calendar.
    cultures = []
    for _ in range(N_VATS_PER_CULTURE):
        cultures.append("Traditional")
        cultures.append("Commercial")

    rows = []
    for index, culture in enumerate(cultures):
        vat_code = "V{:02d}".format(index + 1)
        make_date = SEASON_START + datetime.timedelta(
            days=index * MAKE_DATE_SPACING_DAYS
        )

        culture_mean = MEAN_TRADITIONAL if culture == "Traditional" else MEAN_COMMERCIAL
        vat_true_value = rng.gauss(culture_mean, SD_BETWEEN_VATS)

        for replicate_no in range(1, N_REPLICATES + 1):
            titration = rng.gauss(vat_true_value, SD_WITHIN_SAMPLE)
            rows.append(
                {
                    "VatCode": vat_code,
                    "CultureType": culture,
                    "MakeDate": make_date.isoformat(),
                    "ReplicateNo": replicate_no,
                    "SaltInMoisturePct": "{:.2f}".format(titration),
                }
            )
    return rows


def main():
    rows = build_rows()
    fieldnames = [
        "VatCode",
        "CultureType",
        "MakeDate",
        "ReplicateNo",
        "SaltInMoisturePct",
    ]
    with open(OUTFILE, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote {} rows to {}".format(len(rows), OUTFILE))


if __name__ == "__main__":
    main()
