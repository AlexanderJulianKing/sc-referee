"""Generate the tooth-level probing depth data file for the gingivitis paste trial.

Standard library only. Fixed seed so the file is reproducible byte-for-byte.

Design mirrored by the generator:
  * 26 adult patients with mild chronic gingivitis, randomised as whole people,
    13 to a stannous fluoride paste and 13 to a conventional sodium fluoride paste.
  * 8 index teeth measured per patient at 12 weeks -> 208 rows.
  * Probing depth = arm mean + persistent patient offset + tooth-level noise.
    The patient offset stands in for plaque control and smoking, which push a
    whole mouth up or down together; that is why teeth in one mouth are
    correlated.
  * Bleeding on probing is drawn from a logistic model of the tooth's depth,
    so deeper sites bleed more often.
"""

import csv
import math
import os
import random

SEED = 20260822

# FDI notation. Eight index teeth, spread over all four quadrants.
INDEX_TEETH = ["16", "12", "24", "26", "32", "36", "44", "46"]

N_PER_ARM = 13

ARMS = {
    # arm label -> (mean probing depth mm, clip low, clip high)
    "sodium_fluoride": (3.30, 2.4, 4.2),
    "stannous_fluoride": (2.80, 2.0, 3.6),
}

PATIENT_SD = 0.30   # between-patient spread (plaque control, smoking)
TOOTH_SD = 0.22     # tooth-to-tooth spread inside one mouth

# Logistic model for bleeding on probing, driven by the tooth's depth.
BLEED_INTERCEPT = -4.5
BLEED_SLOPE = 1.3

OUT_NAME = "probing_depth.csv"


def make_patient_codes(rng, n):
    """Anonymised trial codes: two-digit site, three-digit subject, e.g. GNG-02-114."""
    codes = []
    for site in (1, 2, 3):
        for subject in range(101, 141):
            codes.append("GNG-%02d-%03d" % (site, subject))
    rng.shuffle(codes)
    return sorted(codes[:n])


def main():
    rng = random.Random(SEED)

    codes = make_patient_codes(rng, 2 * N_PER_ARM)
    assignment = ["stannous_fluoride"] * N_PER_ARM + ["sodium_fluoride"] * N_PER_ARM
    rng.shuffle(assignment)

    rows = []
    for code, arm in zip(codes, assignment):
        arm_mean, lo, hi = ARMS[arm]
        patient_offset = rng.gauss(0.0, PATIENT_SD)
        for tooth in INDEX_TEETH:
            depth = arm_mean + patient_offset + rng.gauss(0.0, TOOTH_SD)
            depth = min(hi, max(lo, depth))
            depth = round(depth, 1)
            p_bleed = 1.0 / (1.0 + math.exp(-(BLEED_INTERCEPT + BLEED_SLOPE * depth)))
            bleeding = "yes" if rng.random() < p_bleed else "no"
            rows.append([code, arm, tooth, bleeding, "%.1f" % depth])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    with open(out_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["patient_code", "paste_arm", "tooth_site",
             "bleeding_on_probing", "probing_depth_mm"]
        )
        writer.writerows(rows)

    print("wrote %s (%d data rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
