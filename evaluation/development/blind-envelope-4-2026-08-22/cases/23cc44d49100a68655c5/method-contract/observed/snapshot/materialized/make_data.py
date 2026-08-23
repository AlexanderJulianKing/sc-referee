"""Generate the cuttlefish enrichment dataset.

Twenty juvenile common cuttlefish, ten in enriched holdings and ten in bare
holdings, each given six prey-presentation trials on separate days. The outcome
is latency to first tentacle strike in seconds.

Simulation model (trial i on animal j):

    strike_latency_s = group_mean[housing(j)] + animal_effect[j] + trial_noise

    group_mean["enriched"] = 9.6      group_mean["bare"] = 14.2
    animal_effect[j] ~ Normal(0, 3.5)   (between-animal temperament)
    trial_noise      ~ Normal(0, 2.5)   (within-animal trial-to-trial variation)

Values are held inside the recordable range (above 1 s, below 30 s) by
redrawing the trial noise, and are rounded to one decimal place.

Standard library only. The seed is fixed, so the CSV is reproducible.

The seed was chosen from a scan of candidate seeds so that the two realized
group means land close to the 9.6 s and 14.2 s figures the study specifies
(realized: 9.56 s enriched, 14.22 s bare). Everything else is a plain draw from
the model above; no individual value was hand-edited.
"""

import csv
import os
import random

SEED = 2092

GROUP_MEAN = {"enriched": 9.6, "bare": 14.2}
BETWEEN_ANIMAL_SD = 3.5
WITHIN_ANIMAL_SD = 2.5

N_PER_GROUP = 10
N_TRIALS = 6

LOWER_BOUND = 1.0
UPPER_BOUND = 30.0

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuttlefish_strike_latency.csv")


def main():
    rng = random.Random(SEED)

    # Ten enriched animals then ten bare animals, CF-01 .. CF-20.
    housing_by_animal = ["enriched"] * N_PER_GROUP + ["bare"] * N_PER_GROUP

    rows = []
    for index, housing in enumerate(housing_by_animal, start=1):
        animal_ref = "CF-%02d" % index
        base = GROUP_MEAN[housing]

        # Animal-level temperament offset, kept inside +/- 2.5 SD so that no
        # single animal sits implausibly far outside the colony.
        while True:
            animal_effect = rng.gauss(0.0, BETWEEN_ANIMAL_SD)
            if abs(animal_effect) <= 2.5 * BETWEEN_ANIMAL_SD:
                break
        animal_level = base + animal_effect

        for trial_number in range(1, N_TRIALS + 1):
            while True:
                value = animal_level + rng.gauss(0.0, WITHIN_ANIMAL_SD)
                value = round(value, 1)
                if LOWER_BOUND < value < UPPER_BOUND:
                    break
            rows.append([animal_ref, housing, trial_number, "%.1f" % value])

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["animal_ref", "housing", "trial_number", "strike_latency_s"])
        writer.writerows(rows)

    print("wrote %s with %d data rows" % (OUT_PATH, len(rows)))


if __name__ == "__main__":
    main()
