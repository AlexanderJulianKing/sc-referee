"""Generate the synthetic arterial blood gas dataset for the ICU sedation study.

Twenty-four mechanically ventilated adults (12 light sedation, 12 deep sedation)
each contribute six arterial blood gas measurements at 0, 6, 12, 24, 36 and 48
hours from enrolment. The outcome is the PaO2/FiO2 ratio in mmHg.

Generating model (all values synthetic; no real patient data is used):
    PFRatio = arm level + patient offset + time drift + measurement noise
      arm level      : 245 mmHg (light) / 215 mmHg (deep), averaged over the
                       six scheduled time points
      patient offset : Normal(0, 45) drawn once per patient
      time drift     : +15 mmHg linearly from enrolment to 48 hours
      noise          : Normal(0, 30) drawn independently per measurement
    Values are rounded to whole numbers and clipped to 110-400 mmHg.

Standard library only. Fixed seed for reproducibility.
"""

import csv
import os
import random

# Fixed seed. It was chosen from a scan of candidate seeds so that the
# realised arm averages land near the intended 245 / 215 mmHg and no value
# needs clipping at the 110-400 mmHg bounds; the generating model itself is
# unchanged by that choice.
SEED = 20260569

ARM_MEAN = {"light": 245.0, "deep": 215.0}
BETWEEN_PATIENT_SD = 45.0
WITHIN_PATIENT_SD = 30.0
DRIFT_TOTAL = 15.0          # mmHg gained from hour 0 to hour 48
TIME_POINTS = [0, 6, 12, 24, 36, 48]
PF_MIN, PF_MAX = 110, 400

# Twelve light-sedation patients, then twelve deep-sedation patients.
ARMS = ["light"] * 12 + ["deep"] * 12

# The arm means above describe the average across the six scheduled time
# points, so remove the average drift from the intercept.
MEAN_DRIFT = DRIFT_TOTAL * sum(TIME_POINTS) / (len(TIME_POINTS) * max(TIME_POINTS))


def main():
    rng = random.Random(SEED)
    rows = []
    for index, arm in enumerate(ARMS, start=1):
        patient_id = "ICU-%02d" % index
        patient_offset = rng.gauss(0.0, BETWEEN_PATIENT_SD)
        intercept = ARM_MEAN[arm] - MEAN_DRIFT + patient_offset
        for hours in TIME_POINTS:
            drift = DRIFT_TOTAL * hours / max(TIME_POINTS)
            value = intercept + drift + rng.gauss(0.0, WITHIN_PATIENT_SD)
            value = int(round(value))
            value = max(PF_MIN, min(PF_MAX, value))
            rows.append([patient_id, arm, hours, value])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "sedation_abg.csv")
    with open(out_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["PatientID", "SedationArm", "HoursFromEnrolment",
                         "PFRatio"])
        writer.writerows(rows)
    print("wrote %d data rows to %s" % (len(rows), out_path))


if __name__ == "__main__":
    main()
