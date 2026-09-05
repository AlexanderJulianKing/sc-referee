# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded generator (`SEED = 20260826`, Python standard library only) that writes `ra_baseline_markers.csv`. Re-running it reproduces the same table exactly. |
| `ra_baseline_markers.csv` | The analysis input. Baseline blood marker table for the early rheumatoid arthritis cohort, 56 data rows plus one header row, comma separated, UTF-8, no missing cells. |

## `ra_baseline_markers.csv`

**One row represents one patient**: a single stored baseline blood sample drawn
before first-line therapy began, together with that patient's six-month response
classification and the half of the split-sample design the patient was allocated
to. Each patient appears exactly once; there are 56 patients and 56 rows. Every
cell is filled.

Columns, in file order:

| # | Column | Type | Unit | Holds |
| --- | --- | --- | --- | --- |
| 1 | `patient_id` | text | none | Patient identifier, `RA-001` through `RA-056`. Unique across the file. |
| 2 | `group` | text | none | Six-month response status assigned by the treating clinician, blinded to the assays. Exactly two possible entries: `responder` (29 patients) and `non_responder` (27 patients). |
| 3 | `stage` | text | none | The half of the split-sample design the patient was allocated to by the fixed random allocation recorded in the study database before any assay was run. Exactly two possible entries: `discovery` (28 patients: 15 responders, 13 non-responders) and `validation` (28 patients: 14 responders, 14 non-responders). |
| 4 | `crp_mg_l` | number, 1 decimal | mg/L | Baseline C-reactive protein. Values in this file run from 3.2 to 47.2. |
| 5 | `esr_mm_h` | integer | mm/h | Baseline erythrocyte sedimentation rate. Values in this file run from 9 to 72. |
| 6 | `anti_ccp_u_ml` | number, 1 decimal | U/mL | Baseline anti-cyclic citrullinated peptide antibody. Values in this file run from 5.5 to 305.3. |
| 7 | `rf_iu_ml` | number, 1 decimal | IU/mL | Baseline rheumatoid factor. Values in this file run from 8.4 to 218.1. |
| 8 | `calprotectin_ng_ml` | integer | ng/mL | Baseline serum calprotectin. Values in this file run from 941 to 6090. |
| 9 | `vitd_nmol_l` | number, 1 decimal | nmol/L | Baseline serum 25-hydroxyvitamin D. Values in this file run from 30.7 to 92.5. |

Columns 4 through 9 are the six protocol-declared baseline markers, written in
the declared protocol order. Rows are listed in enrolment order, so `group` and
`stage` are interleaved rather than blocked.

## How the values were generated

`make_data.py` draws each marker from a lognormal distribution on the natural
scale, with a centre that depends on the patient's `group` and a spread chosen
to give realistic patient-to-patient variation, then resamples any draw that
falls outside the plausible assay range for that marker and rounds to the
precision a laboratory would report. The two halves are dealt alternately within
each response class after a seeded shuffle, which is what keeps responders and
non-responders in similar proportion in both halves. All randomness comes from a
single `random.Random(SEED)` stream, so the file is deterministic.
