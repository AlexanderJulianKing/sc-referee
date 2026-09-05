# data.csv

Occupational health monitoring of hospital cleaning staff on general wards, comparing two
disinfectant application methods used at the same product concentration.

**One row is one cleaning worker**, measured once at the end of a single monitored shift by the same
occupational hygiene team. There are 58 rows plus a header row: 29 workers in each application
method group. Every worker has a value in every column; there are no blanks.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `worker_id` | text | none | Anonymous identifier for the worker, `W001` through `W058`. Unique in the file. |
| `application_method` | text | none | Application method the worker used during the monitored shift. Exactly two values: `trigger_spray` and `pre_soaked_wipes`. |
| `fev1_l` | number | litres (L) | Declared outcome 1. Forced expiratory volume in one second, measured by spirometry at the end of the shift. |
| `feno_ppb` | number | parts per billion (ppb) | Declared outcome 2. Fractional exhaled nitric oxide at the end of the shift. |
| `airway_symptom_score` | integer | none (0-20 scale) | Declared outcome 3. Airway symptom questionnaire score, where higher means more symptoms. |
| `peak_tvoc_mg_m3` | number | milligrams per cubic metre (mg/m3) | Declared outcome 4. Peak airborne total volatile organic compounds measured on the worker during cleaning. |
| `eye_skin_irritation_score` | integer | none (0-10 scale) | Declared outcome 5. Eye and skin irritation score, where higher means more irritation. |

The five outcome columns appear in the order the five outcomes were declared in the monitoring plan.

## Recorded ranges in this file

- `fev1_l`: 2.41 to 4.10, two decimal places.
- `feno_ppb`: 7.4 to 43.8, one decimal place.
- `airway_symptom_score`: 0 to 12, whole numbers.
- `peak_tvoc_mg_m3`: 0.33 to 3.39, two decimal places.
- `eye_skin_irritation_score`: 0 to 6, whole numbers.

## Provenance

`data.csv` is a fixed authored file. Values were written once to be realistic for this setting and are
not regenerated at analysis time.
