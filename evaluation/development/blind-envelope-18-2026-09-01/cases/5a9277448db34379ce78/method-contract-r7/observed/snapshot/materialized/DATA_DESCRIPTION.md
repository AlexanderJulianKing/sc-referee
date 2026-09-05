# Data description

`data.csv` holds the patient-level record for the stroke unit comparison of two
thickened-liquid protocols. Seventy-two consecutive inpatients with post-stroke
swallowing difficulty were managed for fourteen days on one of the two protocols,
thirty-six per protocol, and were assessed by the same speech and language therapy
team.

**One row is one patient.** The file has 72 data rows plus a header row. Every cell
is filled; there are no blanks and no repeated patient identifiers.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `patient_id` | text | Patient identifier, `PT01` through `PT72`, in admission order. One per patient, no duplicates. |
| `liquid_thickness` | text | The protocol the patient was managed on. Exactly two values: `mildly_thick` (36 patients) and `moderately_thick` (36 patients). |
| `penetration_aspiration_score` | integer | Declared outcome 1. Penetration-aspiration scale score at bedside swallow assessment. An ordered clinical score from 1 to 8, where a lower score means a safer swallow. Observed range in this file: 1 to 6. |
| `mealtime_duration_min` | number | Declared outcome 2. Time taken to complete a meal, in minutes. Observed range: 16.3 to 44.9. |
| `daily_oral_fluid_intake_ml` | integer | Declared outcome 3. Fluid taken by mouth over a day, in millilitres. Observed range: 735 to 1700. |
| `meal_completion_pct` | number | Declared outcome 4. Proportion of the served meal the patient completed, as a percentage from 0 to 100. Observed range: 46.2 to 96.2. |
| `weight_change_kg` | number | Declared outcome 5. Body weight change over the fourteen days, in kilograms. Negative means weight lost, positive means weight gained. Observed range: -3.0 to +1.3. |
| `coughing_episodes_per_meal` | integer | Declared outcome 6. Count of coughing episodes recorded during a meal. Observed range: 0 to 5. |

The six outcome columns appear in the order the protocol declared them, after the
identifier and group columns.
