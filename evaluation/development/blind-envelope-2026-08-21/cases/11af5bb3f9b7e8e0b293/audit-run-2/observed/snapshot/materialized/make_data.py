"""Generate the nubbin calcification data set for the Acropora millepora
thermal-stress experiment.

Design encoded here:
  * 14 wild parent colonies, COL-A ... COL-N.
  * Each whole colony is assigned to one thermal regime (7 ambient, 7 heated).
  * 5 nubbins are cut from each colony -> 70 nubbin rows.
  * Nubbins from the same colony share a genotype, so they share a colony
    baseline calcification rate; only a small within-colony residual separates
    them.

Genotype spread is deliberately built to be at least as large as the average
regime difference: the colony baseline standard deviation is 0.24 mg/g/day
while the ambient-minus-heated regime offset is 0.22 mg/g/day.

Run:  python3 make_data.py
"""

import csv
import string

import numpy as np

SEED = 20261187
N_COLONIES = 14
N_PER_REGIME = 7
N_NUBBINS = 5

# Population-level calcification (mg CaCO3 per g skeleton per day).
AMBIENT_MEAN = 1.000
HEATED_OFFSET = -0.220          # average regime difference
COLONY_SD = 0.240               # genotype (parent colony) spread >= |offset|
RESIDUAL_SD = 0.070             # nubbin-to-nubbin noise within a colony

RATE_MIN, RATE_MAX = 0.400, 1.600
WEIGHT_MIN, WEIGHT_MAX = 4.0, 12.0

OUT_PATH = "nubbin_calcification.csv"


def main() -> None:
    rng = np.random.default_rng(SEED)

    colonies = ["COL-" + letter for letter in string.ascii_uppercase[:N_COLONIES]]

    # Assign whole colonies to regimes: alternate so both regimes span the
    # alphabet, then the assignment is fixed by the seed-independent pattern.
    regimes = []
    for i in range(N_COLONIES):
        regimes.append("ambient" if i % 2 == 0 else "heated")
    assert regimes.count("ambient") == N_PER_REGIME
    assert regimes.count("heated") == N_PER_REGIME

    # One baseline per parent colony (the genotype effect).
    colony_baselines = rng.normal(0.0, COLONY_SD, size=N_COLONIES)

    rows = []
    for colony, regime, baseline in zip(colonies, regimes, colony_baselines):
        colony_mean = AMBIENT_MEAN + baseline
        if regime == "heated":
            colony_mean += HEATED_OFFSET
        for k in range(1, N_NUBBINS + 1):
            initial_weight = float(rng.uniform(WEIGHT_MIN, WEIGHT_MAX))
            rate = colony_mean + float(rng.normal(0.0, RESIDUAL_SD))
            rate = min(max(rate, RATE_MIN), RATE_MAX)
            rows.append(
                {
                    "parent_colony": colony,
                    "thermal_regime": regime,
                    "nubbin_code": "n{}".format(k),
                    "initial_weight_g": "{:.2f}".format(initial_weight),
                    "calcification_rate": "{:.3f}".format(rate),
                }
            )

    with open(OUT_PATH, "w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "parent_colony",
                "thermal_regime",
                "nubbin_code",
                "initial_weight_g",
                "calcification_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("wrote {} rows to {}".format(len(rows), OUT_PATH))


if __name__ == "__main__":
    main()
