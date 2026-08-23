"""Generate the synthetic referral waiting-time audit data.

Twenty-six primary care clinics: 13 on a centralised booking protocol and 13 on
local booking arrangements. Eight consecutive referrals audited per clinic.

Waiting times are drawn from a two-level model:
    waiting_days = clinic_mean + within-clinic noise
    clinic_mean  = protocol mean + between-clinic noise
with protocol means of 21 days (local) and 17 days (centralised), a between-clinic
standard deviation of 5 days and a within-clinic standard deviation of 6 days.

Outputs (written next to this script):
    referral_audit.csv   one row per audited referral (208 rows)
    clinic_summary.csv   one row per clinic (26 rows)

Run: /usr/local/bin/python3 make_data.py
"""

import csv
import os
import random

SEED = 20260822

N_CLINICS_PER_ARM = 13
N_REFERRALS_PER_CLINIC = 8

PROTOCOL_MEANS = {"local": 21.0, "centralised": 17.0}
SD_BETWEEN_CLINICS = 5.0
SD_WITHIN_CLINIC = 6.0

MIN_WAIT_DAYS = 1

AGE_BANDS = ["18-39", "40-59", "60-74", "75+"]
AGE_BAND_WEIGHTS = [0.22, 0.30, 0.30, 0.18]

SPECIALTIES = [
    "cardiology",
    "dermatology",
    "gastroenterology",
    "orthopaedics",
    "ophthalmology",
    "ear_nose_throat",
]
SPECIALTY_WEIGHTS = [0.18, 0.20, 0.15, 0.20, 0.15, 0.12]

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "referral_audit.csv")
SUMMARY_PATH = os.path.join(HERE, "clinic_summary.csv")


def build_rows(rng):
    raw_rows = []
    summary_rows = []

    clinic_number = 0
    # Clinics are numbered in a single sequence and the two protocols are
    # interleaved, so the identifier does not encode the assignment.
    protocol_sequence = []
    for i in range(N_CLINICS_PER_ARM):
        protocol_sequence.append("local")
        protocol_sequence.append("centralised")
    rng.shuffle(protocol_sequence)

    for protocol in protocol_sequence:
        clinic_number += 1
        clinic_id = "CL{:02d}".format(clinic_number)

        clinic_mean = rng.gauss(PROTOCOL_MEANS[protocol], SD_BETWEEN_CLINICS)

        waits = []
        for referral_number in range(1, N_REFERRALS_PER_CLINIC + 1):
            wait = rng.gauss(clinic_mean, SD_WITHIN_CLINIC)
            wait_days = max(MIN_WAIT_DAYS, int(round(wait)))
            waits.append(wait_days)

            raw_rows.append(
                {
                    "clinic_id": clinic_id,
                    "booking_protocol": protocol,
                    "referral_id": "{}-R{}".format(clinic_id, referral_number),
                    "waiting_days": wait_days,
                    "patient_age_band": rng.choices(AGE_BANDS, AGE_BAND_WEIGHTS)[0],
                    "referral_specialty": rng.choices(SPECIALTIES, SPECIALTY_WEIGHTS)[0],
                }
            )

        summary_rows.append(
            {
                "clinic_id": clinic_id,
                "booking_protocol": protocol,
                "n_referrals_audited": len(waits),
                "mean_waiting_days": round(sum(waits) / len(waits), 3),
            }
        )

    return raw_rows, summary_rows


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rng = random.Random(SEED)
    raw_rows, summary_rows = build_rows(rng)

    write_csv(
        RAW_PATH,
        [
            "clinic_id",
            "booking_protocol",
            "referral_id",
            "waiting_days",
            "patient_age_band",
            "referral_specialty",
        ],
        raw_rows,
    )
    write_csv(
        SUMMARY_PATH,
        ["clinic_id", "booking_protocol", "n_referrals_audited", "mean_waiting_days"],
        summary_rows,
    )

    print("wrote {} ({} rows)".format(RAW_PATH, len(raw_rows)))
    print("wrote {} ({} rows)".format(SUMMARY_PATH, len(summary_rows)))


if __name__ == "__main__":
    main()
