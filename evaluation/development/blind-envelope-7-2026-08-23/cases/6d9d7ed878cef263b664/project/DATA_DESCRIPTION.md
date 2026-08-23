# Data description

## File

`phosphate_data.csv` — the single data file for this study. Plain text, comma
separated, one header line plus 144 data lines.

## What one row is

One row is **one patient at one mid-week study session**: the pre-dialysis
serum phosphate result for that patient in that study week.

## Units and size

- 18 patients on thrice-weekly maintenance haemodialysis.
- 8 consecutive study weeks per patient, one blood draw each week, taken before
  the mid-week dialysis session.
- 18 patients x 8 weeks = **144 rows**. Every patient has all 8 weeks; there are
  no missing values.

## The two groups

Patients were on one of two oral phosphate-binder regimens, 9 patients in each:

| `binder_regimen` value | Regimen | Patients | Rows |
| --- | --- | --- | --- |
| `calcium_acetate` | the established binder | 9 | 72 |
| `sucroferric_oxyhydroxide` | the newer binder | 9 | 72 |

A patient stays on the same binder for all 8 weeks, so the regimen is a
patient-level property that is repeated on each of that patient's 8 rows.
Patients HD-01, HD-03, ... HD-17 (odd numbers) are on the established binder;
HD-02, HD-04, ... HD-18 (even numbers) are on the newer binder.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Study identifier for the patient, `HD-01` through `HD-18`. Appears on 8 rows, one per study week. |
| `binder_regimen` | text | Which oral phosphate binder the patient was on: `calcium_acetate` (established) or `sucroferric_oxyhydroxide` (newer). Constant within a patient. |
| `study_week` | integer | Which study week the sample came from, 1 to 8, counting consecutive weeks from the start of the observation period. |
| `serum_phosphate_mmol_l` | number, 2 decimals | Pre-dialysis serum phosphate concentration in millimoles per litre (mmol/L) for that patient in that week. |

## Observed range

All 144 phosphate values lie between 0.97 and 2.48 mmol/L, inside the
clinically plausible window for a dialysis population. By arm: 1.06 to 2.48
mmol/L on the established binder, 0.97 to 2.19 mmol/L on the newer binder.

## How the file was made

`make_data.py` writes `phosphate_data.csv` using only the Python standard
library and a fixed random seed (20260952), so re-running it reproduces the
same file. For each patient the phosphate value in a given week is an arm mean
(1.90 mmol/L established, 1.55 mmol/L newer) plus a patient offset drawn once
per patient (SD 0.35 mmol/L, the between-patient spread) plus independent
week-to-week noise (SD 0.18 mmol/L, the within-patient spread). Values are
rounded to 2 decimals the way a hospital laboratory reports them. The committed
CSV is the data of record; nothing regenerates it at analysis time.
