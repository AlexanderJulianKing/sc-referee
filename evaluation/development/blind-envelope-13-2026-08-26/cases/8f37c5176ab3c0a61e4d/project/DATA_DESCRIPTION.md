# Data description

## File

`screen_time_cohort.csv` — 96 data rows plus one header row.

## What one row represents

One row is one adolescent. Each of the 96 adolescents, aged 14 to 16, was measured once at a
single morning fasting visit, so a row holds that adolescent's group label, their analysis half,
and their six outcome measurements from that one visit. No adolescent appears twice.

## Columns

Columns appear in the file in the order listed here.

| Column | Meaning | Unit | Type and values |
| --- | --- | --- | --- |
| `participant_id` | Identifier for the adolescent | none | Text, `ADO-001` through `ADO-096`, unique |
| `screen_time_group` | Recreational screen time group, assigned in advance from four weeks of device-recorded screen use | none | Text, exactly two values: `high`, `low` (48 adolescents each) |
| `analysis_half` | Which half of the fixed random allocation the adolescent falls in | none | Text, exactly two values: `discovery`, `validation` (48 adolescents each) |
| `bmi_z_score` | Body mass index z-score for age and sex | none (z-score) | Number, 2 decimals |
| `waist_circumference_cm` | Waist circumference | centimetres | Number, 1 decimal |
| `fasting_insulin_miu_l` | Fasting insulin | milli-international units per litre | Number, 1 decimal |
| `fasting_triglycerides_mmol_l` | Fasting triglycerides | millimoles per litre | Number, 2 decimals |
| `hdl_cholesterol_mmol_l` | HDL cholesterol | millimoles per litre | Number, 2 decimals |
| `alt_u_l` | Alanine aminotransferase | units per litre | Number, 1 decimal |

The six outcome columns are stored in the order the outcomes were declared in the analysis plan:
BMI z-score, waist circumference, fasting insulin, fasting triglycerides, HDL cholesterol, alanine
aminotransferase.

## Completeness and balance

- 96 rows, no blank cells. Every adolescent has a value in every outcome column.
- `screen_time_group`: 48 `high`, 48 `low`.
- `analysis_half`: 48 `discovery`, 48 `validation`.
- The two groups are balanced within each half: 24 `high` and 24 `low` in `discovery`, and 24
  `high` and 24 `low` in `validation`.
- Rows are stored in shuffled order, so the file is not sorted by group or by half.

## Observed ranges

| Column | Minimum | Maximum |
| --- | --- | --- |
| `bmi_z_score` | -1.63 | 2.51 |
| `waist_circumference_cm` | 63.1 | 100.4 |
| `fasting_insulin_miu_l` | 3.8 | 28.7 |
| `fasting_triglycerides_mmol_l` | 0.52 | 2.07 |
| `hdl_cholesterol_mmol_l` | 0.55 | 2.15 |
| `alt_u_l` | 5.7 | 54.7 |

## Provenance

The measurements are invented, not collected from real adolescents. They were produced by
`generate_data.py` in this directory with a fixed seed, so the file can be reproduced exactly.
Insulin, triglycerides, and ALT were drawn on a log scale to give the right-skewed upper tail those
measures show in real cohorts; the other three were drawn symmetrically. Within each adolescent the
six outcomes share a common per-person term, so an adolescent who is larger on one adiposity-linked
measure tends to be larger on the related ones, with HDL running in the opposite direction. Values
were kept inside plausible physiological limits for this age range.
