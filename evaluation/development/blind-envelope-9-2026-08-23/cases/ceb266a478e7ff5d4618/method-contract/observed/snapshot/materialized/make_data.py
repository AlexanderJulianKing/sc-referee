"""Generate the raw cluster-level Brix data for the blueberry inoculation trial.

Twenty-four potted highbush blueberry bushes, twelve inoculated at planting and
twelve left uninoculated, grown in one polytunnel. At harvest five separate
berry clusters were picked from each bush and the juice of each cluster was
read on a refractometer, giving 5 x 24 = 120 cluster rows.

Structure of the simulated values:
  bush level    : a random bush offset, SD 0.9 degrees Brix
  cluster level : measurement/cluster noise, SD 0.4 degrees Brix
  treatment     : inoculated bushes run 0.7 degrees Brix higher on average

Standard library only. Fixed seed so the CSV is reproducible.
"""

import csv
import os
import random

SEED = 20260823

N_BUSHES = 24
N_INOCULATED = 12
CLUSTERS_PER_BUSH = 5

CONTROL_MEAN_BRIX = 11.9    # uninoculated bush mean, degrees Brix
INOCULATION_EFFECT = 0.7    # added to inoculated bushes, degrees Brix
BETWEEN_BUSH_SD = 0.9       # bush-to-bush variation, degrees Brix
WITHIN_BUSH_SD = 0.4        # cluster-to-cluster variation on one bush

OUT_NAME = "blueberry_brix_clusters.csv"


def main():
    rng = random.Random(SEED)

    bush_labels = ["BB-%02d" % i for i in range(1, N_BUSHES + 1)]

    # Randomly assign twelve bushes to the inoculated group.
    assigned = bush_labels[:]
    rng.shuffle(assigned)
    inoculated = set(assigned[:N_INOCULATED])

    rows = []
    for label in bush_labels:
        treatment = "inoculated" if label in inoculated else "uninoculated"
        bush_mean = CONTROL_MEAN_BRIX + rng.gauss(0.0, BETWEEN_BUSH_SD)
        if treatment == "inoculated":
            bush_mean += INOCULATION_EFFECT
        for cluster in range(1, CLUSTERS_PER_BUSH + 1):
            brix = bush_mean + rng.gauss(0.0, WITHIN_BUSH_SD)
            # Refractometer reads to one decimal place.
            rows.append({
                "bush_label": label,
                "treatment": treatment,
                "cluster_number": cluster,
                "soluble_solids_brix": "%.1f" % round(brix, 1),
            })

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    fields = ["bush_label", "treatment", "cluster_number", "soluble_solids_brix"]
    with open(out_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("wrote %d rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
