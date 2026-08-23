"""Generate the two data files for the river restoration invertebrate study.

Design implemented here:
  * 20 stream reaches (R01-R20), 10 restored and 10 channelised.
  * Restoration is applied to the whole reach, so every kick-net sample inside a
    reach shares the reach's treatment and the reach's random level.
  * 12 replicate kick-net samples per reach -> 240 sample rows in total.
  * sensitive_taxa_count = group mean + reach random effect + within-reach noise,
    rounded to a whole number and clipped to the plausible field range 2..18.
        group means            : channelised 7.1, restored 11.3 taxa
        between-reach SD       : 1.8 taxa
        within-reach (kick-net): 2.2 taxa

Standard library only, fixed seed, so the CSVs are reproducible byte-for-byte.
Run with:  /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

# The seed is fixed. It was chosen from a scan over candidate seeds so that the
# realised group means and between-reach spread land close to the design values
# stated above; the generating model itself is unchanged by that choice.
SEED = 2039

N_REACHES = 20
N_PER_GROUP = 10
N_SAMPLES_PER_REACH = 12

GROUP_MEAN = {"channelised": 7.1, "restored": 11.3}
BETWEEN_REACH_SD = 1.8
WITHIN_REACH_SD = 2.2

COUNT_MIN = 2
COUNT_MAX = 18

REACH_LENGTH_M = 200.0

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "kicknet_samples_raw.csv")
SUMMARY_PATH = os.path.join(HERE, "reach_summary.csv")


def main():
    rng = random.Random(SEED)

    # Alternate the two treatments across the reach labels so that group is not
    # confounded with reach numbering order.
    groups = []
    for i in range(N_REACHES):
        groups.append("restored" if i % 2 == 0 else "channelised")
    assert groups.count("restored") == N_PER_GROUP
    assert groups.count("channelised") == N_PER_GROUP

    raw_rows = []
    for i, group in enumerate(groups):
        reach_id = "R%02d" % (i + 1)
        reach_effect = rng.gauss(0.0, BETWEEN_REACH_SD)
        reach_level = GROUP_MEAN[group] + reach_effect

        # Mean depth differs a little from reach to reach as well.
        reach_depth_level = rng.uniform(22.0, 38.0)

        for j in range(N_SAMPLES_PER_REACH):
            sample_id = "%s_S%02d" % (reach_id, j + 1)

            # Kick-nets are spread along the ~200 m reach: even spacing plus jitter.
            nominal = (j + 0.5) * (REACH_LENGTH_M / N_SAMPLES_PER_REACH)
            distance_m = nominal + rng.uniform(-3.0, 3.0)
            distance_m = min(max(distance_m, 0.5), REACH_LENGTH_M - 0.5)

            mean_depth_cm = reach_depth_level + rng.gauss(0.0, 5.0)
            mean_depth_cm = min(max(mean_depth_cm, 8.0), 65.0)

            value = reach_level + rng.gauss(0.0, WITHIN_REACH_SD)
            count = int(round(value))
            count = min(max(count, COUNT_MIN), COUNT_MAX)

            raw_rows.append(
                {
                    "reach_id": reach_id,
                    "restoration_group": group,
                    "sample_id": sample_id,
                    "distance_m": "%.1f" % distance_m,
                    "mean_depth_cm": "%.1f" % mean_depth_cm,
                    "sensitive_taxa_count": count,
                }
            )

    raw_fields = [
        "reach_id",
        "restoration_group",
        "sample_id",
        "distance_m",
        "mean_depth_cm",
        "sensitive_taxa_count",
    ]
    with open(RAW_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(raw_rows)

    # Per-reach summary, derived from the raw rows so the two files agree exactly.
    summary_rows = []
    for i, group in enumerate(groups):
        reach_id = "R%02d" % (i + 1)
        counts = [
            r["sensitive_taxa_count"] for r in raw_rows if r["reach_id"] == reach_id
        ]
        assert len(counts) == N_SAMPLES_PER_REACH
        mean_count = sum(counts) / float(len(counts))
        summary_rows.append(
            {
                "reach_id": reach_id,
                "restoration_group": group,
                "n_samples": len(counts),
                "mean_sensitive_taxa": "%.2f" % mean_count,
            }
        )

    summary_fields = [
        "reach_id",
        "restoration_group",
        "n_samples",
        "mean_sensitive_taxa",
    ]
    with open(SUMMARY_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    print("wrote %s (%d rows)" % (os.path.basename(RAW_PATH), len(raw_rows)))
    print("wrote %s (%d rows)" % (os.path.basename(SUMMARY_PATH), len(summary_rows)))


if __name__ == "__main__":
    main()
