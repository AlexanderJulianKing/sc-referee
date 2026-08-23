"""Generate the leaf-cutter ant forager load dataset.

Design (see DATA_DESCRIPTION.md):
  16 queenright colonies, 8 exposed to a sublethal fungicide dose and 8 unexposed
  controls. The colony is the experimental unit: the fungicide was delivered through
  the colony's forage supply, so every worker in a colony shares one exposure.
  10 returning foragers were intercepted per colony -> 160 weighed foragers.

Target structure written into the numbers:
  control colony mean fragment mass   22.5 mg
  exposed colony mean fragment mass   18.4 mg
  between-colony SD                    2.2 mg
  within-colony (forager) SD           4.0 mg

Run with:  /usr/local/bin/python3 make_data.py
Writes:    forager_loads.csv  (one row per intercepted forager)
"""

import csv
import os

import numpy as np

SEED = 20260822
N_COLONIES = 16
N_PER_GROUP = 8
N_FORAGERS = 10

MEAN_CONTROL_MG = 22.5
MEAN_EXPOSED_MG = 18.4
SD_BETWEEN_COLONY_MG = 2.2
SD_WITHIN_COLONY_MG = 4.0

# Head width of a forager, in mm. Media workers on the foraging trail run roughly
# 1.5-2.4 mm across the head. Larger workers cut and carry larger fragments, so a
# modest head-width term is folded into the within-colony variation rather than
# added on top of it (see SD_RESIDUAL_MG below).
MEAN_HEAD_WIDTH_MM = 1.95
SD_HEAD_WIDTH_MM = 0.18
BETA_HEAD_WIDTH = 2.0  # mg of fragment mass per mm of head width

# Within-colony variation is split between the head-width term and unstructured
# forager noise so that the two together total SD_WITHIN_COLONY_MG.
SD_RESIDUAL_MG = float(
    np.sqrt(SD_WITHIN_COLONY_MG**2 - (BETA_HEAD_WIDTH * SD_HEAD_WIDTH_MM) ** 2)
)

# Foraging activity in the arenas was scored between 07:00 and 19:00.
FIRST_HOUR = 7
LAST_HOUR = 19

OUT_NAME = "forager_loads.csv"
COLUMNS = [
    "colony_id",
    "exposure_group",
    "forager_id",
    "head_width_mm",
    "interception_hour",
    "fragment_mass_mg",
]


def main():
    rng = np.random.default_rng(SEED)

    # Alternate treatment labels across colony numbers so that group is not
    # confounded with the C01..C16 ordering.
    groups = ["control" if i % 2 == 0 else "exposed" for i in range(N_COLONIES)]
    assert groups.count("control") == N_PER_GROUP
    assert groups.count("exposed") == N_PER_GROUP

    # One random intercept per colony, centred within each group so the realised
    # group means stay close to the targets above.
    colony_effects = rng.normal(0.0, SD_BETWEEN_COLONY_MG, size=N_COLONIES)
    for label in ("control", "exposed"):
        idx = [i for i, g in enumerate(groups) if g == label]
        colony_effects[idx] -= colony_effects[idx].mean()

    rows = []
    for i in range(N_COLONIES):
        colony_id = "C%02d" % (i + 1)
        group = groups[i]
        group_mean = MEAN_CONTROL_MG if group == "control" else MEAN_EXPOSED_MG
        colony_level = group_mean + colony_effects[i]

        for j in range(N_FORAGERS):
            head_width = rng.normal(MEAN_HEAD_WIDTH_MM, SD_HEAD_WIDTH_MM)
            head_width = float(np.clip(head_width, 1.40, 2.60))
            hour = int(rng.integers(FIRST_HOUR, LAST_HOUR + 1))

            # Redraw the (rare) non-positive fragment mass rather than truncating it,
            # so no mass piles up at a floor value.
            for _ in range(100):
                mass = (
                    colony_level
                    + BETA_HEAD_WIDTH * (head_width - MEAN_HEAD_WIDTH_MM)
                    + rng.normal(0.0, SD_RESIDUAL_MG)
                )
                if mass > 0:
                    break
            if mass <= 0:
                raise RuntimeError("could not draw a positive fragment mass")

            rows.append(
                {
                    "colony_id": colony_id,
                    "exposure_group": group,
                    "forager_id": "F%02d" % (j + 1),
                    "head_width_mm": round(head_width, 2),
                    "interception_hour": hour,
                    "fragment_mass_mg": round(float(mass), 1),
                }
            )

    assert len(rows) == N_COLONIES * N_FORAGERS
    assert all(r["fragment_mass_mg"] > 0 for r in rows)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %s (%d rows)" % (out_path, len(rows)))

    # Console check that the intended structure survived rounding.
    masses = np.array([r["fragment_mass_mg"] for r in rows])
    labels = np.array([r["exposure_group"] for r in rows])
    colonies = np.array([r["colony_id"] for r in rows])
    for label in ("control", "exposed"):
        sel = labels == label
        print("  %-8s n=%3d  mean=%5.2f mg" % (label, sel.sum(), masses[sel].mean()))
    colony_means = np.array([masses[colonies == c].mean() for c in sorted(set(colonies))])
    within = np.concatenate(
        [masses[colonies == c] - masses[colonies == c].mean() for c in sorted(set(colonies))]
    )
    colony_group = np.array(
        [labels[colonies == c][0] for c in sorted(set(colonies))]
    )
    centred = np.concatenate(
        [
            colony_means[colony_group == g] - colony_means[colony_group == g].mean()
            for g in ("control", "exposed")
        ]
    )
    print("  between-colony SD (within group) = %.2f mg" % centred.std(ddof=1))
    print("  within-colony SD                 = %.2f mg" % within.std(ddof=1))
    print("  min fragment mass                = %.1f mg" % masses.min())


if __name__ == "__main__":
    main()
