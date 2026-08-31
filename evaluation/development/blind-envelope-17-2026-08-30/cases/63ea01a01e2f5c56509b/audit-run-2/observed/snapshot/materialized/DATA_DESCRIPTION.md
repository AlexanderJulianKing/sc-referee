# Data description: sleep_study_data.csv

## What one row represents

One row is one randomised patient: an adult with chronic insomnia disorder enrolled in the sleep
clinic trial, with the support they were randomised to and their week-eight outcome values. There
are 70 rows, one per patient, 35 in each group. Every patient has a value for every outcome; there
are no missing cells and no repeated patients.

The four sleep-diary outcomes are each the patient's average over a two-week diary kept at week
eight. The insomnia severity index score is taken from one questionnaire completed at week eight.

## Columns

The file has a header row and seven columns, in this order.

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Patient identifier: the prefix `P` plus a zero-padded two-digit serial number, `P01` through `P70`. Unique within the file. |
| `group` | text | Which support the patient was randomised to. Exactly two distinct values: `booklet` (sleep-hygiene information booklet, no guidance) and `digital_cbti` (six-week guided digital cognitive behavioural therapy programme for insomnia). |
| `sleep_onset_latency_min` | integer | Declared outcome 1. Sleep onset latency: minutes from lights out to falling asleep, rounded to the nearest minute. |
| `wake_after_sleep_onset_min` | integer | Declared outcome 2. Wake after sleep onset: minutes spent awake between falling asleep and the final waking, rounded to the nearest minute. |
| `total_sleep_time_min` | integer | Declared outcome 3. Total sleep time per night in minutes, rounded to the nearest minute. |
| `sleep_efficiency_pct` | number, one decimal place | Declared outcome 4. Sleep efficiency: total sleep time as a percentage of time in bed. |
| `insomnia_severity_index_score` | integer | Declared outcome 5. Insomnia severity index total score on the 0 to 28 scale, where a higher score means worse insomnia. |

Columns 3 through 7 are the five outcome variables of the declared outcome family, listed here in
the order the protocol declared them.

## Observed ranges in the file

These are whole-file ranges across all 70 patients, given so a reader can see the scale of each
column.

| Column | Minimum | Maximum |
| --- | --- | --- |
| `sleep_onset_latency_min` | 12 | 86 |
| `wake_after_sleep_onset_min` | 12 | 136 |
| `total_sleep_time_min` | 249 | 493 |
| `sleep_efficiency_pct` | 56.0 | 94.9 |
| `insomnia_severity_index_score` | 3 | 28 |

## Notes

- The values are fixed and committed in the CSV. Nothing in the analysis is generated at run time.
- The diary quantities for a patient are internally consistent: sleep efficiency is total sleep time
  as a share of that patient's time in bed, and time in bed also covers the sleep onset latency, the
  wake after sleep onset, and any time awake in bed before getting up.
