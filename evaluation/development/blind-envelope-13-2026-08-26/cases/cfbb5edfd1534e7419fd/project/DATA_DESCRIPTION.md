# Data description: mandibular advancement device study

File: `mad_device_study.csv` (50 data rows plus one header row)

## What one row represents

One row is one adult participant with moderate obstructive sleep apnoea, holding that person's
device assignment and the five protocol outcomes measured in a single overnight home sleep study
after eight weeks of device use. Each participant appears exactly once; there are no repeated
measurements and no blank cells.

Fifty participants took part, 25 fitted with each device design.

## Columns, in file order

| Column | Meaning | Unit or scale |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant, `P001` through `P050` | Identifier, no unit |
| `device_group` | Which mandibular advancement device design the participant was fitted with. Exactly two values: `custom_titratable_two_piece` (custom titratable two-piece device) and `prefabricated_one_piece` (prefabricated one-piece device) | Categorical label, no unit |
| `ahi_events_per_hour` | Apnoea-hypopnoea index: apnoeas and hypopnoeas recorded per hour of sleep. Declared outcome 1 | Events per hour |
| `odi_events_per_hour` | Oxygen desaturation index: qualifying oxygen desaturation events per hour of sleep. Declared outcome 2 | Events per hour |
| `epworth_sleepiness_score_0_24` | Epworth Sleepiness Scale total score reported by the participant; higher means more daytime sleepiness. Declared outcome 3 | Integer points on a 0 to 24 scale |
| `min_oxygen_saturation_percent` | Lowest pulse-oximetry oxygen saturation reached at any point during the overnight study. Declared outcome 4 | Percent |
| `sleep_efficiency_percent` | Time asleep as a share of time in bed. Declared outcome 5 | Percent |

The five outcome columns appear in the order they were declared in the study protocol before
recruitment.

## Known data quality note

Participant `P032` has a recorded `min_oxygen_saturation_percent` of 62.4, which is implausibly low
for this population. The sleep technician's note attributes it to the pulse oximeter probe slipping
off the finger for part of the night, so the reading reflects a detached sensor rather than the
participant's true overnight nadir. The value is kept in the CSV exactly as recorded. Every other
value in the file is within the clinically plausible range for these measurements.
