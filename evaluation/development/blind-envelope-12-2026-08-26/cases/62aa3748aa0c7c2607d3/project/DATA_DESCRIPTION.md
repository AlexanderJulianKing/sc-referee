# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic, seeded Python generator (standard library only, seed 20260826). Running it rewrites `mobilisation_trial.csv` byte for byte. |
| `mobilisation_trial.csv` | The analysis input: one row per enrolled patient, 70 data rows plus a header row. |

## `mobilisation_trial.csv`

**What one row represents.** One enrolled patient after elective heart valve
surgery: the schedule that patient followed, and that patient's five protocol
outcomes recorded at the single day-of-discharge assessment. Each patient
appears exactly once. There are 70 rows, 35 patients on the standard schedule
and 35 on the accelerated schedule. Every cell is filled; there are no blanks
and no missing-value codes. Rows are in enrolment order, so the two schedules
are mixed through the file rather than blocked.

**Columns**, in file order:

| Column | Type | Unit | What it holds |
| --- | --- | --- | --- |
| `patient_id` | text | none | Patient identifier, `P01` through `P70`, unique across the file. Also the enrolment position. |
| `group` | text | none | The mobilisation schedule the patient followed. Exactly two possible entries: `standard` (first sits out of bed on the first postoperative day) and `accelerated` (mobilisation begins on the evening of surgery). |
| `walk_distance_m` | integer | metres | Outcome 1. Six-minute walk distance at discharge. Observed range in this file: 151 to 451. |
| `length_of_stay_days` | integer | days | Outcome 2. Postoperative hospital length of stay, counted from the day of surgery to the day of discharge. Observed range: 4 to 15. |
| `mip_cmh2o` | integer | centimetres of water | Outcome 3. Maximal inspiratory pressure at discharge, recorded as a positive number. Observed range: 29 to 92. |
| `pain_nrs` | integer | points on a 0 to 10 scale | Outcome 4. Pain at rest on the day of discharge, on the 0 to 10 numerical rating scale (0 is no pain, 10 is worst imaginable pain). Observed range: 1 to 9. |
| `days_to_stairs` | integer | days | Outcome 5. Days from surgery to the first independent stair climb. Observed range: 2 to 11. |

The five outcome columns appear in the order the protocol declared them.

## How the values were made

`make_data.py` draws each patient from a group-specific centre with shared
spread, so only the centre differs between the two schedules. One latent
per-patient recovery factor moves all five outcomes together, which is why a
patient who walks further also tends to stay fewer days and reach the stairs
sooner. Three patients in each arm are drawn as slower, complicated recoveries:
shorter walk, longer stay, weaker inspiratory pressure, more pain, later stairs.
Draws that would fall outside the clinically plausible range are compressed
towards the limit rather than cut off at it, so extreme values crowd near the
edges instead of piling up exactly on them. All five outcomes are rounded to
whole numbers, matching how they are charted at the bedside.

These are synthetic values. No real patient data is involved.
