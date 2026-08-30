# Data description

## File

`tinnitus_sound_therapy.csv` — 70 data rows plus one header row.

## What one row represents

One row is one participant in the randomised study of sound therapy for chronic
subjective tinnitus: a single adult with tinnitus of at least six months
duration, holding that participant's therapy allocation and their five declared
outcome measurements taken at the week-twelve assessment. Each participant
appears exactly once. There are no repeated measures in the file, and no missing
values: every participant has a number in every outcome column.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `pid` | text | Per-participant identifier, `p01` through `p70`. Unique within the file. |
| `noise_type` | text | Therapy allocation. Exactly two values: `notched` (individually shaped notched-noise therapy, 35 participants) and `broadband` (unmodified broadband noise therapy, 35 participants). |
| `thi_pts` | integer | Outcome 1. Tinnitus handicap inventory total score at week twelve, in points on a 0 to 100 scale. Higher is worse. Item scores of 0, 2 and 4 make every total an even number. |
| `loudness_pts` | number, 1 decimal | Outcome 2. Tinnitus loudness rating at week twelve, in points on a 0 to 10 visual analogue scale. Higher is louder. |
| `sleep_idx_pts` | integer | Outcome 3. Sleep quality index score at week twelve, in points on a 0 to 21 scale. Higher is worse sleep. |
| `anxiety_pts` | integer | Outcome 4. Anxiety subscale score at week twelve, in points on a 0 to 21 scale. Higher is worse. |
| `mml_db` | number, 1 decimal | Outcome 5. Minimum masking level at week twelve, in decibels sensation level (dB SL). Higher means more noise is needed to mask the tinnitus. |

The five outcome columns appear in the order the protocol declared them, left to
right, after the identifier and allocation columns.

## Units and naming

Column names are lower case with words joined by underscores. Each outcome
column carries its unit as a suffix: `_pts` for points on a rating or
questionnaire scale, `_db` for decibels sensation level.
