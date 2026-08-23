"""Generate the vineyard rootstock x powdery mildew leaf dataset.

Trial layout: one block, 16 grapevines of the same scion variety.
  - 8 vines grafted onto the estate's standard rootstock
  - 8 vines grafted onto a drought-tolerant rootstock
At veraison, 8 leaves were collected per vine (4 upper canopy, 4 lower canopy)
and mildew lesion area per leaf was measured by image analysis.

Target structure of the invented values:
  standard rootstock mean lesion area      ~ 3.9 cm2 per leaf
  drought-tolerant rootstock mean          ~ 2.4 cm2 per leaf
  vine-to-vine spread (SD of vine means)   ~ 1.1 cm2
  leaf-to-leaf spread within a vine (SD)   ~ 1.6 cm2
  total leaf area                          ~ 95 cm2 per leaf

Run with: /usr/local/bin/python3 make_data.py
Writes mildew_leaf_data.csv next to this script. No third-party packages.
"""

import csv
import os
import random

SEED = 20260330

N_VINES_PER_ROOTSTOCK = 8
LEAVES_PER_VINE = 8
POSITIONS = ["Upper", "Lower"]  # 4 leaves each per vine

ROOTSTOCK_MEAN = {
    "Standard": 3.9,
    "DroughtTolerant": 2.4,
}
VINE_SD = 1.1       # between-vine spread in lesion area
LEAF_SD = 1.6       # leaf-to-leaf spread within one vine
MIN_VINE_MEAN = 0.7   # floor on a vine's average lesion area, cm2

LEAF_AREA_MEAN = 95.0
LEAF_AREA_SD = 11.0

OUT_NAME = "mildew_leaf_data.csv"
HEADER = ["Vine", "Rootstock", "CanopyPosition", "Leaf", "LesionArea", "TotalLeafArea"]


def leaf_lesion(rng, vine_mean, leaf_sd):
    """Draw one leaf's lesion area for a vine whose average is vine_mean.

    Lesion area cannot be negative and a few heavily infected leaves sit well
    above the rest, so the leaf-to-leaf draw uses a gamma distribution shaped
    to the requested mean and standard deviation instead of a normal one.
    """
    shape = (vine_mean / leaf_sd) ** 2
    scale = (leaf_sd ** 2) / vine_mean
    return rng.gammavariate(shape, scale)


def vine_offsets(rng, n_vines, target_sd):
    """Draw one lesion-area offset per vine, then recentre and rescale them.

    With only eight vines per rootstock a raw draw can leave the group mean
    well away from the intended rootstock mean, so the offsets are shifted to
    mean zero and rescaled to the intended vine-to-vine standard deviation.
    """
    raw = [rng.gauss(0.0, target_sd) for _ in range(n_vines)]
    mean = sum(raw) / n_vines
    centred = [value - mean for value in raw]
    sd = (sum(value * value for value in centred) / (n_vines - 1)) ** 0.5
    scale = target_sd / sd
    return [value * scale for value in centred]


def build_rows(seed):
    """Build every data row for the trial from one fixed seed."""
    rng = random.Random(seed)
    rows = []
    vine_number = 0

    for rootstock in ("Standard", "DroughtTolerant"):
        offsets = vine_offsets(rng, N_VINES_PER_ROOTSTOCK, VINE_SD)
        for vine_index in range(N_VINES_PER_ROOTSTOCK):
            vine_number += 1
            vine_id = "V%02d" % vine_number
            # one offset per vine: vines differ appreciably from each other
            vine_mean = ROOTSTOCK_MEAN[rootstock] + offsets[vine_index]
            if vine_mean < MIN_VINE_MEAN:
                # even a lightly infected vine carries some mildew at veraison
                vine_mean = MIN_VINE_MEAN

            leaf_number = 0
            for position in POSITIONS:
                for _ in range(LEAVES_PER_VINE // len(POSITIONS)):
                    leaf_number += 1
                    lesion = leaf_lesion(rng, vine_mean, LEAF_SD)
                    leaf_area = rng.gauss(LEAF_AREA_MEAN, LEAF_AREA_SD)
                    rows.append([
                        vine_id,
                        rootstock,
                        position,
                        "%s-L%d" % (vine_id, leaf_number),
                        round(lesion, 2),
                        round(leaf_area, 1),
                    ])

    return rows


def main():
    rows = build_rows(SEED)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
