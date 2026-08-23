"""Generate the trial dataset for the stage 3 CKD sodium-counselling study.

Standard library only, fixed seed, so the CSV regenerates byte-for-byte.

Design encoded here:
  24 participants, 12 per arm, 6 monthly follow-up visits each -> 144 rows.
  Usual advice arm centred near 134 mmHg, intensive counselling arm near 128 mmHg.
  Between-participant SD 9 mmHg (a stable offset per person), within-participant
  SD 5 mmHg (visit-to-visit variation on the same person), so differences between
  people are larger than the drift within one person across visits.
  Age and baseline eGFR are drawn once per participant and repeat across that
  participant's six rows. eGFR is held inside the stage 3 CKD band (30-59).
"""

import csv
import os
import random

SEED = 4802
N_PER_ARM = 12
N_VISITS = 6

ARM_MEAN = {"usual_advice": 134.0, "intensive_counselling": 128.0}
BETWEEN_SD = 9.0   # spread between participants
WITHIN_SD = 5.0    # visit-to-visit variation inside one participant

FIELDS = [
    "participant_id",
    "trial_arm",
    "visit_number",
    "systolic_bp_mmhg",
    "age_years",
    "baseline_egfr_ml_min_1_73m2",
]


def truncated_gauss(rng, mu, sd, lo, hi):
    """Normal draw resampled until it falls in [lo, hi]."""
    for _ in range(200):
        x = rng.gauss(mu, sd)
        if lo <= x <= hi:
            return x
    return min(hi, max(lo, x))


def build_rows():
    rng = random.Random(SEED)
    rows = []
    pid = 0

    for arm in ("usual_advice", "intensive_counselling"):
        for _ in range(N_PER_ARM):
            pid += 1
            participant_id = "P%02d" % pid

            person_mean = ARM_MEAN[arm] + rng.gauss(0.0, BETWEEN_SD)
            visit_bps = [person_mean + rng.gauss(0.0, WITHIN_SD)
                         for _ in range(N_VISITS)]

            # stable participant characteristics, drawn once per person
            age_years = int(round(truncated_gauss(rng, 63.0, 9.0, 41.0, 84.0)))
            baseline_egfr = round(truncated_gauss(rng, 44.0, 7.5, 30.0, 59.0), 1)

            for visit, sbp in enumerate(visit_bps, start=1):
                rows.append({
                    "participant_id": participant_id,
                    "trial_arm": arm,
                    "visit_number": visit,
                    "systolic_bp_mmhg": round(sbp, 1),
                    "age_years": age_years,
                    "baseline_egfr_ml_min_1_73m2": baseline_egfr,
                })

    return rows


def main():
    rows = build_rows()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ckd_sodium_trial_bp.csv")
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %s (%d rows)" % (out_path, len(rows)))


if __name__ == "__main__":
    main()
