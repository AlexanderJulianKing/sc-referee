# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded generator (`SEED = 20260856`, NumPy). Running it writes `migraine_trial.csv`. Re-running reproduces the same file. |
| `migraine_trial.csv` | The study data file. 88 data rows plus one header row, 9 columns, comma separated, UTF-8. |

## What one row represents

One row is one randomised participant, and each participant appears exactly once.
The outcome values on that row summarise that participant's headache diary over the
final four weeks of the twelve-week treatment period. There are 88 rows: 44
participants on the medicine and 44 on placebo. Every cell is filled; there are no
missing values.

## Columns in `migraine_trial.csv`

Columns appear in this order. The seven outcome columns are in the protocol's
declared order.

| # | Column | Type | Range in this file | What it holds |
| --- | --- | --- | --- | --- |
| 1 | `participant_id` | text | `MIG-001` to `MIG-088` | Unique participant identifier. 88 distinct values. |
| 2 | `monthly_headache_days` | integer, days per 4 weeks | 0 to 14 | Number of days in the final four weeks on which the participant recorded any headache. |
| 3 | `monthly_migraine_attacks` | integer, attacks per 4 weeks | 0 to 8 | Number of distinct migraine attacks recorded in the final four weeks. Never larger than `monthly_headache_days` for the same participant, because an attack occupies at least one headache day. |
| 4 | `peak_pain_intensity_0_10` | decimal, 0 to 10 scale | 0.0 to 10.0 | The participant's worst recorded pain intensity, on a 0 (no pain) to 10 (worst imaginable) diary scale, recorded to one decimal place. A participant with no headache days has no pain to rate and is recorded as 0.0. |
| 5 | `rescue_medication_days_per_month` | integer, days per 4 weeks | 0 to 10 | Number of days in the final four weeks on which acute rescue medication was taken. Never larger than `monthly_headache_days` for the same participant. |
| 6 | `migraine_disability_score_0_60` | integer, 0 to 60 scale | 0 to 44 | Migraine-related disability score covering the final four weeks, on a 0 (no disability) to 60 (most disability) scale. |
| 7 | `nausea_days_per_month` | integer, days per 4 weeks | 0 to 6 | Number of days in the final four weeks with recorded nausea. Never larger than `monthly_headache_days` for the same participant. |
| 8 | `sleep_quality_index_0_21` | integer, 0 to 21 scale | 1 to 18 | Sleep quality index for the final four weeks, on a 0 to 21 scale where a higher score means worse sleep. |
| 9 | `treatment_arm` | text, exactly two values | `medicine`, `placebo` | The arm the participant was randomised to. 44 rows carry `medicine` and 44 carry `placebo`. |

## How the values were produced

`make_data.py` draws each participant's outcomes from normal distributions centred
on the arm level stated in the study description, with the stated between-participant
spread. Part of each outcome's variation comes from one shared per-participant
severity factor, so a participant who has a heavy month on one diary outcome tends to
have a heavy month on the others too. Values are then put on their recording scale:
diary counts and questionnaire scores are rounded to whole numbers, the pain rating is
rounded to one decimal place, and every value is clipped to the range its instrument
allows. Attack, rescue-medication, and nausea day counts are additionally capped at
the participant's own headache-day count.
