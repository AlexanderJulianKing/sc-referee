# Data description

Two comma-separated files support this study of referral waiting times across primary care
clinics. Both were produced by `make_data.py` (Python 3, standard library only, fixed random
seed `20260822`), and the summary file is derived from the raw file, so the two are consistent
by construction.

## Units and groups

The **clinic** is the unit that was assigned to a booking protocol. Twenty-six clinics in one
region took part. Thirteen adopted the **centralised** booking protocol and thirteen kept their
**local** booking arrangements. Clinic identifiers run from `CL01` to `CL26`; the protocols are
shuffled across that sequence, so the identifier carries no information about the assignment.

Within each clinic, eight consecutive patient referrals were audited. Audited referrals are
records drawn from inside a clinic, not independently assigned units. Total audited referrals:
26 clinics x 8 referrals = 208, split 104 under each protocol.

## `referral_audit.csv` — the raw audit

**One row = one audited patient referral.** 208 data rows plus one header row; 6 columns.

| column | type | description |
| --- | --- | --- |
| `clinic_id` | text | Clinic identifier, `CL01` to `CL26`. The unit of assignment. Appears 8 times, once per audited referral. |
| `booking_protocol` | text | `centralised` or `local`. Constant within a clinic. |
| `referral_id` | text | Referral record identifier, formed as `<clinic_id>-R<n>` with `n` from 1 to 8. Unique across the file. |
| `waiting_days` | integer | Days from referral to first specialist appointment. Observed range 1 to 43. |
| `patient_age_band` | text | One of `18-39`, `40-59`, `60-74`, `75+`. Counts in the file: 40, 73, 58, 37. |
| `referral_specialty` | text | One of `cardiology`, `dermatology`, `gastroenterology`, `orthopaedics`, `ophthalmology`, `ear_nose_throat`. Counts in the file: 40, 43, 32, 30, 35, 28. |

## `clinic_summary.csv` — the per-clinic curation summary

**One row = one clinic.** 26 data rows plus one header row; 4 columns. This file was prepared
during data curation by aggregating `referral_audit.csv`.

| column | type | description |
| --- | --- | --- |
| `clinic_id` | text | Clinic identifier, `CL01` to `CL26`. Unique in this file; the key that links to the raw audit. |
| `booking_protocol` | text | `centralised` or `local`, matching the raw file. 13 clinics in each group. |
| `n_referrals_audited` | integer | Number of audited referrals contributing to that clinic's row. 8 for every clinic. |
| `mean_waiting_days` | number | That clinic's average `waiting_days` across its 8 audited referrals, rounded to 3 decimal places. Observed range 8.75 to 33.5. |

## How the waiting times were generated

Waiting times follow a two-level model, which is the structure the design implies: referrals sit
inside clinics, and clinics differ from one another.

1. Each clinic gets its own average wait, drawn around the protocol average with a standard
   deviation of 5 days between clinics. The protocol averages are 21 days for local arrangements
   and 17 days for centralised booking.
2. Each of the clinic's 8 referrals is drawn around that clinic's own average with a standard
   deviation of 6 days within a clinic.
3. Each draw is rounded to a whole number of days and floored at a minimum of 1 day, since a wait
   cannot be zero or negative. Five of the 208 values sit at that floor of 1 day, so the low end
   of the distribution is very slightly compressed relative to the model.

Realised group averages of the per-clinic means are 20.47 days (local, standard deviation 6.98
across the 13 clinics) and 16.48 days (centralised, standard deviation 4.53). These are one
random realisation, so they differ a little from the 21 and 17 day targets.

## Consistency check

For every clinic, `n_referrals_audited` equals the count of that clinic's rows in
`referral_audit.csv`, and `mean_waiting_days` equals the mean of that clinic's `waiting_days`
values in `referral_audit.csv` to 3 decimal places. `booking_protocol` agrees between the two
files for every clinic.

## Regenerating

    /usr/local/bin/python3 make_data.py

The seed is fixed, so the same two files are reproduced byte for byte.
