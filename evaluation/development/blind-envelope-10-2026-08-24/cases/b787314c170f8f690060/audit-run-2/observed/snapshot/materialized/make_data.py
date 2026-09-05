"""Deterministic generator for the pulmonary rehabilitation delivery-format dataset.

Creates pulmonary_rehab_outcomes.csv: one row per patient, one column per declared
outcome, plus a patient identifier and the programme-format group label.

Run:
    python make_data.py
"""

import csv
import os

import numpy as np

SEED = 20260824
N_PER_GROUP = 37
GROUPS = ("centre_based", "home_based")

OUT_NAME = "pulmonary_rehab_outcomes.csv"

# Per-group generating parameters for each outcome.
# (mean_centre_based, mean_home_based, within-group sd, low bound, high bound)
OUTCOME_PARAMS = {
    # Six-minute walk distance, metres. Centre-based supervision gives a modest edge.
    "six_min_walk_m": (392.0, 358.0, 62.0, 180.0, 520.0),
    # COPD assessment test, 0-40, higher is worse. Formats are close together.
    "cat_score": (18.4, 19.1, 5.4, 8.0, 34.0),
    # Quadriceps isometric peak torque, newton metres. Formats are close together.
    "quad_torque_nm": (88.0, 85.5, 19.5, 40.0, 140.0),
    # Thirty-second sit-to-stand repetitions. Centre-based has a modest edge.
    "sit_to_stand_reps": (14.9, 13.1, 3.4, 6.0, 26.0),
}

# Correlation between the four outcomes on the latent scale. Patients who walk
# further tend to be stronger, do more repetitions, and report fewer symptoms
# (cat_score is reverse-scored, so it carries negative correlations).
LATENT_CORR = np.array(
    [
        [1.00, -0.55, 0.52, 0.60],
        [-0.55, 1.00, -0.38, -0.45],
        [0.52, -0.38, 1.00, 0.47],
        [0.60, -0.45, 0.47, 1.00],
    ]
)

OUTCOME_ORDER = ["six_min_walk_m", "cat_score", "quad_torque_nm", "sit_to_stand_reps"]


def draw_group(rng, group, n):
    """Draw n correlated patient records for one programme format."""
    means = np.array(
        [
            OUTCOME_PARAMS[name][0 if group == "centre_based" else 1]
            for name in OUTCOME_ORDER
        ]
    )
    sds = np.array([OUTCOME_PARAMS[name][2] for name in OUTCOME_ORDER])
    cov = LATENT_CORR * np.outer(sds, sds)

    rows = []
    while len(rows) < n:
        candidate = rng.multivariate_normal(means, cov)
        in_range = all(
            OUTCOME_PARAMS[name][3] <= value <= OUTCOME_PARAMS[name][4]
            for name, value in zip(OUTCOME_ORDER, candidate)
        )
        if in_range:
            rows.append(candidate)
    return np.array(rows)


def main():
    rng = np.random.default_rng(SEED)

    centre = draw_group(rng, "centre_based", N_PER_GROUP)
    home = draw_group(rng, "home_based", N_PER_GROUP)

    labels = [GROUPS[0]] * N_PER_GROUP + [GROUPS[1]] * N_PER_GROUP
    values = np.vstack([centre, home])

    # Shuffle so that the file is not sorted by group, then assign sequential ids.
    order = rng.permutation(len(labels))
    labels = [labels[i] for i in order]
    values = values[order]

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "patient_id",
                "program_group",
                "six_min_walk_m",
                "cat_score",
                "quad_torque_nm",
                "sit_to_stand_reps",
            ]
        )
        for index, (label, row) in enumerate(zip(labels, values), start=1):
            walk, cat, torque, sts = row
            writer.writerow(
                [
                    "PR-{:03d}".format(index),
                    label,
                    int(round(walk)),
                    int(round(cat)),
                    "{:.1f}".format(torque),
                    int(round(sts)),
                ]
            )

    print("wrote {} rows to {}".format(len(labels), out_path))


if __name__ == "__main__":
    main()
