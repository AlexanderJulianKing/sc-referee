# Data description

File: `levothyroxine_formulation_trial.csv`

## What one row represents

One row is one randomised patient, holding that patient's week-twelve
measurements. Each patient appears exactly once. The file has a header row and
64 data rows: 64 adults with primary hypothyroidism, already on a stable tablet
dose, randomised for twelve weeks at an unchanged microgram dose. Thirty-two
patients stayed on the standard tablet and thirty-two switched to the oral
liquid formulation. Every patient has a value for every outcome; there are no
missing cells and no extra rows.

All four outcome values in a row come from the same week-twelve visit: the
bloods drawn at that visit and the questionnaire completed at it.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Patient identifier: the prefix `pt_` plus a zero-padded two-digit serial number, `pt_01` through `pt_64`. Unique across the file. |
| `group` | text | Formulation the patient was randomised to. Exactly two distinct values: `tablet` (standard tablet) and `liquid` (oral liquid). Thirty-two rows each. |
| `tsh_miu_l` | number, 2 decimals | Serum thyroid stimulating hormone at week twelve, in milli-international units per litre. |
| `free_t4_pmol_l` | number, 1 decimal | Serum free thyroxine at week twelve, in picomoles per litre. |
| `total_cholesterol_mmol_l` | number, 2 decimals | Total cholesterol at week twelve, in millimoles per litre. |
| `symptom_score_0_40` | integer | Hypothyroid symptom questionnaire score at week twelve, on a 0 to 40 scale. Higher means more symptoms. |

The four outcome columns appear in the declared order fixed in the trial
protocol before randomisation: thyroid stimulating hormone, free thyroxine,
total cholesterol, symptom score.

Values are rounded to the precision a hospital laboratory report or a
questionnaire would give.

## Note on one recorded value

Patient `pt_60`, in the tablet group, has a week-twelve thyroid stimulating
hormone of 14.20 milli-international units per litre, far above every other
patient in the file (the next highest value is 5.00). The clinic reads this as
likely missed doses in the run-up to the visit rather than a formulation
effect. It is a real recorded measurement and it is present in the data file.
