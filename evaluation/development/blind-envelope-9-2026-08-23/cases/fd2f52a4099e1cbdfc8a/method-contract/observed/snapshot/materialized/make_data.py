"""Generate the simulated reaction-time data for the sustained-attention training study.

Design
------
22 volunteers, 11 in each of two four-week training regimes:
  * "adaptive"        - adaptive working-memory training
  * "active_control"  - untimed puzzles (active control)

Each volunteer completes 12 trials of the same simple visual reaction-time task
in a single session, so the table holds 22 * 12 = 264 rows.

Generating model (a random-intercept structure, matching how the data are analysed):
  reaction_time_ms = group_mean(group) + volunteer_offset[v] + trial_noise
    volunteer_offset ~ Normal(0, 45)   between-volunteer SD, ms
    trial_noise      ~ Normal(0, 35)   within-volunteer SD, ms
Group means are 407 ms (adaptive) and 432 ms (active control), i.e. the adaptive
regime is 25 ms faster on average. Values are recorded to 0.1 ms, as the timing
routine reports them.

With only 11 volunteers per group, a raw draw of the volunteer offsets leaves a
large sampling error in the between-volunteer spread and shifts the group means
away from their intended separation. The offsets are therefore centred and
rescaled within each group so that the realised between-volunteer SD is 45 ms and
the group separation is the intended 25 ms; the trial-level noise is left
untouched, so every row still carries ordinary independent measurement error.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

SEED = 20260823

N_PER_GROUP = 11
N_TRIALS = 12

GROUP_MEAN_MS = {"adaptive": 407.0, "active_control": 432.0}
BETWEEN_VOLUNTEER_SD_MS = 45.0
WITHIN_VOLUNTEER_SD_MS = 35.0

OUT_NAME = "reaction_times.csv"


def main() -> None:
    rng = random.Random(SEED)

    # Volunteers V01..V22; alternate the group assignment so that neither group
    # occupies a single block of reference numbers (as in the lab's enrolment log).
    volunteers = []
    for i in range(1, 2 * N_PER_GROUP + 1):
        group = "adaptive" if i % 2 == 1 else "active_control"
        volunteers.append(("V%02d" % i, group))

    # Draw the volunteer offsets, then centre and rescale them within each group
    # to the intended between-volunteer SD (see module docstring).
    raw = {ref: rng.gauss(0.0, BETWEEN_VOLUNTEER_SD_MS) for ref, _ in volunteers}
    offsets = {}
    for group in GROUP_MEAN_MS:
        refs = [ref for ref, g in volunteers if g == group]
        vals = [raw[ref] for ref in refs]
        mean = sum(vals) / len(vals)
        sd = (sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
        scale = BETWEEN_VOLUNTEER_SD_MS / sd
        for ref in refs:
            offsets[ref] = (raw[ref] - mean) * scale

    rows = []
    for volunteer_ref, group in volunteers:
        base = GROUP_MEAN_MS[group] + offsets[volunteer_ref]
        for trial in range(1, N_TRIALS + 1):
            rt = base + rng.gauss(0.0, WITHIN_VOLUNTEER_SD_MS)
            rows.append(
                {
                    "volunteer_ref": volunteer_ref,
                    "training_regime": group,
                    "trial_number": trial,
                    "reaction_time_ms": round(rt, 1),
                }
            )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "volunteer_ref",
                "training_regime",
                "trial_number",
                "reaction_time_ms",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    values = [r["reaction_time_ms"] for r in rows]
    print("wrote %s: %d rows" % (out_path, len(rows)))
    print("min %.1f  max %.1f  mean %.1f" % (min(values), max(values), sum(values) / len(values)))


if __name__ == "__main__":
    main()
