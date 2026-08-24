"""Generate the simulated dolphin signature-whistle dataset.

Eighteen photo-identified adult bottlenose dolphins of known sex (nine males,
nine females) from one estuary. Each animal contributes six good-quality
whistle recordings from separate encounters, giving 108 rows.

Structure of the invented numbers:
  * each dolphin gets its own characteristic whistle level (between-animal
    spread about 1.8 kHz), so its six recordings resemble each other;
  * each recording adds ordinary measurement noise (within-animal spread
    about 0.9 kHz);
  * females sit about 1.6 kHz above males.

Standard library only. Fixed seed, so the file is reproducible.
"""

import csv
import os
import random

SEED = 20260823

N_PER_SEX = 9
N_RECORDINGS = 6

MALE_MEAN_KHZ = 11.2          # male population mean peak frequency
FEMALE_OFFSET_KHZ = 1.6       # females average this much higher
BETWEEN_ANIMAL_SD_KHZ = 1.8   # animal-to-animal spread
WITHIN_ANIMAL_SD_KHZ = 0.9    # recording-to-recording spread within an animal

OUT_NAME = "whistle_recordings.csv"


def main():
    rng = random.Random(SEED)

    # Nine males then nine females, catalogue ids EST-001 .. EST-018.
    animals = []
    for i in range(N_PER_SEX * 2):
        sex = "male" if i < N_PER_SEX else "female"
        mean = MALE_MEAN_KHZ + (FEMALE_OFFSET_KHZ if sex == "female" else 0.0)
        animal_level = rng.gauss(mean, BETWEEN_ANIMAL_SD_KHZ)
        animals.append(
            {
                "dolphin_catalogue_id": "EST-%03d" % (i + 1),
                "sex": sex,
                "level": animal_level,
            }
        )

    rows = []
    for animal in animals:
        for k in range(1, N_RECORDINGS + 1):
            value = animal["level"] + rng.gauss(0.0, WITHIN_ANIMAL_SD_KHZ)
            rows.append(
                {
                    "dolphin_catalogue_id": animal["dolphin_catalogue_id"],
                    "sex": animal["sex"],
                    "recording_number": k,
                    "peak_frequency_khz": round(value, 2),
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dolphin_catalogue_id",
                "sex",
                "recording_number",
                "peak_frequency_khz",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    values = [r["peak_frequency_khz"] for r in rows]
    print("wrote %s (%d rows)" % (out_path, len(rows)))
    print("peak_frequency_khz range: %.2f to %.2f" % (min(values), max(values)))


if __name__ == "__main__":
    main()
