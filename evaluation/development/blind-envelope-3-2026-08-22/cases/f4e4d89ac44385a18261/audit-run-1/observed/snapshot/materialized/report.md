# Referral waiting times under centralised versus local booking

A health-services audit of 26 primary care clinics in one region

---

## 1. Data description

The study rests on two comma-separated files held in the project folder. They describe the same
audit at two different levels, and the summary file is derived from the raw file, so the two agree
by construction.

### `referral_audit.csv` — the raw audit

**One row represents one audited patient referral.** The file holds 208 data rows and one header
row, with six columns.

| column | description |
| --- | --- |
| `clinic_id` | Clinic identifier, `CL01` to `CL26`. Each clinic appears eight times, once per audited referral. |
| `booking_protocol` | `centralised` or `local`. Constant within a clinic. |
| `referral_id` | Referral record identifier, formed as `<clinic_id>-R<n>` with `n` from 1 to 8. Unique across the file. |
| `waiting_days` | Whole days from referral to first specialist appointment. |
| `patient_age_band` | One of `18-39`, `40-59`, `60-74`, `75+`. |
| `referral_specialty` | One of `cardiology`, `dermatology`, `gastroenterology`, `orthopaedics`, `ophthalmology`, `ear_nose_throat`. |

### `clinic_summary.csv` — the per-clinic curation summary

**One row represents one clinic.** The file holds 26 data rows and one header row, with four
columns. It was prepared during data curation by aggregating the raw audit file.

| column | description |
| --- | --- |
| `clinic_id` | Clinic identifier, `CL01` to `CL26`. Unique in this file, and the key that links back to the raw audit. |
| `booking_protocol` | `centralised` or `local`, matching the raw file. Thirteen clinics in each group. |
| `n_referrals_audited` | Number of audited referrals contributing to that clinic's row. Eight for every clinic. |
| `mean_waiting_days` | That clinic's average `waiting_days` across its eight audited referrals, to three decimal places. |

The analysis script re-derives the per-clinic counts, per-clinic means and protocol labels from
`referral_audit.csv` and compares them against `clinic_summary.csv`. All 26 clinics matched on all
three checks, with no clinic present in one file and absent from the other.

---

## 2. Study design

Twenty-six primary care clinics in a single region took part. Thirteen adopted a centralised
booking protocol and thirteen retained their existing local booking arrangements. The protocol was
adopted by a whole clinic, so **the clinic is the unit that was assigned to a group and is
therefore the independent experimental unit**.

Within each clinic, eight consecutive patient referrals were audited, and the number of days from
referral to first specialist appointment was recorded for each. These eight referrals are repeated
records taken from inside one clinic. They share that clinic's staffing, local specialist capacity
and booking habits, so they are not independent of one another and cannot be treated as 208
independent observations. Treating them that way would inflate the apparent sample size roughly
eightfold and produce a p-value that is too small.

The outcome is the waiting time in days. The comparison of interest is centralised booking against
local arrangements.

---

## 3. Methods

**Which file supplied what.** The inferential comparison was run entirely on
`clinic_summary.csv`, the per-clinic file. Each row there is one clinic, which is the unit that was
assigned to a protocol, so the rows entering the test are independent of one another. The raw
referral-level file `referral_audit.csv` was used **only for descriptive counts** — how many
referrals were audited in total, how many per clinic, and the age-band and specialty composition of
the audited caseload. No referral-level row entered the two-group test.

**The test.** The two groups of clinics were compared with an independent two-sample t-test on
`mean_waiting_days`, the per-clinic average waiting time. Welch's form was used as the primary
test, because it does not assume the two groups share a variance and the observed between-clinic
spread differed between the arms. The sample size is the number of clinics in each group, 13 and
13, not the number of referrals. A 95% confidence interval for the difference in group means was
computed on the same Welch standard error and degrees of freedom.

Two sensitivity checks were run on the same 26 clinic rows: the equal-variance (Student) t-test,
and the distribution-free Mann-Whitney U test. Both use the clinic as the unit of analysis.

Analysis was carried out in Python 3 with pandas and scipy. The script is `analysis.py` at the root
of the project folder, and it prints the descriptive counts and the test result as separate blocks.

---

## 4. Results

### Descriptive counts (from the raw audit file)

A total of **208 referrals** were audited across **26 clinics**, exactly **8 referrals per clinic**
(minimum 8, maximum 8), split evenly at 104 referrals under each protocol. All 208 referral
identifiers were distinct. Observed waiting times ranged from 1 to 43 days.

The audited caseload broke down by patient age band as 40 referrals aged 18-39, 73 aged 40-59, 58
aged 60-74 and 37 aged 75 or over. By specialty it was 40 cardiology, 43 dermatology, 32
gastroenterology, 30 orthopaedics, 35 ophthalmology and 28 ear, nose and throat.

These counts describe the audit only. They played no part in the test below.

### Per-clinic waiting times (from the summary file)

| booking protocol | clinics | mean of clinic means | SD of clinic means | median | range of clinic means |
| --- | --- | --- | --- | --- | --- |
| centralised | 13 | 16.48 days | 4.53 | 15.25 | 10.38 to 27.00 |
| local | 13 | 20.47 days | 6.98 | 19.50 | 8.75 to 33.50 |

Clinic-level variation was substantial in both arms. The slowest centralised clinic (27.0 days
average) waited longer than seven of the thirteen local clinics, and the fastest local clinic (8.75
days average) was quicker than every centralised clinic.

### Two-group comparison

| quantity | value |
| --- | --- |
| n (clinics per group) | 13 centralised, 13 local |
| difference in means, centralised minus local | **-3.99 days** |
| standard error of the difference | 2.31 days |
| 95% confidence interval | **-8.80 to +0.82 days** |
| Welch t | -1.729 on 20.60 degrees of freedom |
| **p-value** | **0.099** |
| Cohen's d (pooled) | -0.68 |

Sensitivity checks agreed. The equal-variance t-test gave t = -1.729 on 24 degrees of freedom,
p = 0.097. The Mann-Whitney U test gave U = 54.0, p = 0.124.

---

## 5. Conclusion

Clinics using centralised booking recorded an average wait about **4.0 days shorter** than clinics
on local arrangements, 16.5 days against 20.5 days. That is the direction the centralised protocol
was intended to produce, and the effect size is moderate (d = -0.68).

**The difference did not reach statistical significance at the conventional 5% level (p = 0.099),
so this audit does not establish that centralised booking shortened waits.** The 95% confidence
interval runs from an 8.8 day reduction to a 0.8 day increase. It is consistent with a worthwhile
clinical benefit, and it is also consistent with essentially no benefit. The honest reading is that
the audit points towards a reduction without demonstrating one.

The limiting factor is the number of clinics, not the number of referrals. With 13 clinics per arm
and a between-clinic standard deviation of roughly 5 to 7 days, the study has limited power to
detect a difference of this size. Auditing more referrals inside the same 26 clinics would sharpen
each clinic's average a little, but it would not add independent units and so would not fix the
power problem. A study designed to settle the question would need substantially more clinics per
arm.

Two further cautions apply. The audit is observational at the clinic level: clinics chose whether
to adopt centralised booking, so the two groups may differ in ways that also affect waiting times,
such as local specialist capacity or baseline demand. And the audited caseload was not balanced by
design across specialties or age bands, so any specialty-specific effect on waiting times is
uncontrolled here.

**Recommendation.** Treat centralised booking as promising but unproven on this evidence. If the
question matters for regional policy, extend the audit to more clinics rather than to more
referrals within the clinics already enrolled, and record clinic-level covariates such as local
specialist capacity so the comparison can be adjusted.
