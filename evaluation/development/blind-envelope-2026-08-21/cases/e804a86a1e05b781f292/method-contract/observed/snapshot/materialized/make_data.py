"""Generate the microcolony_growth.csv dataset for the pollen-diversity experiment.

Fixed seed so the file is reproducible. One row per microcolony, 24 colonies total:
12 on a monofloral (willow) diet and 12 on a mixed four-species pollen diet.
Each colony was weighed exactly once, at week 6.
"""

import csv
import os

import numpy as np

SEED = 20260821
N_PER_GROUP = 12
SHELVES = ["SH-1", "SH-2", "SH-3"]

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "microcolony_growth.csv")


def main() -> None:
    rng = np.random.default_rng(SEED)

    # Balanced design: 12 colonies per diet, and every shelf carries
    # 4 monofloral and 4 mixed colonies (8 colonies per shelf).
    diets = ["monofloral"] * N_PER_GROUP + ["mixed"] * N_PER_GROUP
    shelves = []
    for diet_block in range(2):
        for shelf in SHELVES:
            shelves.extend([shelf] * 4)
    del diet_block

    # Shuffle which physical colony label got which diet/shelf combination,
    # keeping the diet-shelf pairing intact so the balance survives.
    pairs = list(zip(diets, shelves))
    order = rng.permutation(len(pairs))
    pairs = [pairs[i] for i in order]

    rows = []
    for idx, (diet, shelf) in enumerate(pairs, start=1):
        label = f"MC-{idx:02d}"

        # Workers seeded at establishment: small founding groups of 4-6.
        start_workers = int(rng.integers(4, 7))

        # Six-week colony mass. Mixed-pollen colonies average heavier, but both
        # groups are broadly spread because microcolonies are genuinely variable.
        if diet == "mixed":
            mean, sd = 68.0, 14.5
        else:
            mean, sd = 55.0, 13.0

        # Slight, realistic gain from starting with more workers.
        mass = rng.normal(mean, sd) + 1.8 * (start_workers - 5)
        mass = float(np.clip(mass, 35.0, 95.0))

        rows.append(
            {
                "hive_label": label,
                "pollen_diet": diet,
                "start_worker_count": start_workers,
                "rearing_shelf": shelf,
                "final_colony_mass_g": round(mass, 1),
            }
        )

    # Rows are already in MC-01 .. MC-24 order; sort defensively.
    rows.sort(key=lambda r: r["hive_label"])

    fieldnames = [
        "hive_label",
        "pollen_diet",
        "start_worker_count",
        "rearing_shelf",
        "final_colony_mass_g",
    ]
    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
