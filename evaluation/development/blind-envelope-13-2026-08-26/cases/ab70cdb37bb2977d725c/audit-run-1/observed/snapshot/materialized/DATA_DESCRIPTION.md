# Data description

File: `gout_titration_outcomes.csv`

One row is one adult participant in the gout titration study, assessed once at the
six-month review. There are 58 rows plus a header row: 29 participants on the rapid
titration schedule and 29 on the slow schedule. Every participant has a value in every
outcome column, so there are no blank cells.

The five outcome columns appear in the order the study protocol declared them.

## Columns

| Column | Meaning | Unit or scale |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant, one per row, format `GT-001` to `GT-058` | identifier, no unit |
| `titration_schedule` | Urate-lowering titration schedule the participant was on: `rapid` (dose increases every two weeks) or `slow` (dose increases every six weeks) | two-level group label |
| `serum_urate_umol_l` | Declared outcome 1: serum urate at the six-month review | micromoles per litre (umol/L) |
| `gout_flares_past_3_months_count` | Declared outcome 2: number of gout flares in the three months before the review | count of flares (whole number) |
| `egfr_ml_min_1_73m2` | Declared outcome 3: estimated glomerular filtration rate | millilitres per minute per 1.73 square metres |
| `crp_mg_l` | Declared outcome 4: C-reactive protein | milligrams per litre (mg/L) |
| `worst_joint_pain_0_10_scale` | Declared outcome 5: worst joint pain in the past week | 0 to 10 numeric rating scale, whole number, 0 = no pain, 10 = worst imaginable |

## Notes

- The values are invented for this exercise, not measurements from real patients.
- Values were drawn from normal distributions with clinically plausible centres and
  spreads, then held inside plausible clinical limits. Flare counts and pain scores were
  rounded to whole numbers.
- `generate_data.py` in this directory is the script that produced the CSV. It uses a
  fixed random seed, so rerunning it reproduces the same file.
