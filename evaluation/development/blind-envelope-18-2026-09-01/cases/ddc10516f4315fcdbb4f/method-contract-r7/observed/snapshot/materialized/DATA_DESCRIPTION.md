# data.csv

## What one row is

One row is one participating household, observed for one full cooking day by the
same field team, with one symptom questionnaire completed by that household's
main cook. There are 100 rows plus a header row: 50 households cooking on the
improved biomass stove and 50 cooking on a traditional open fire. Every
household has a value in every column; there are no blanks. Households appear in
mixed order rather than grouped by stove type.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `household_id` | text | none | Household identifier, `HH001` through `HH100`. Unique across the file. |
| `stove_type` | text | none | Study group. Exactly two values: `improved_biomass_stove` and `traditional_open_fire`. |
| `kitchen_pm25_ug_m3` | number | micrograms per cubic metre | Declared outcome 1. Twenty-four hour kitchen fine particulate matter concentration. |
| `kitchen_co_ppm` | number | parts per million | Declared outcome 2. Twenty-four hour kitchen carbon monoxide concentration. |
| `fuelwood_use_kg_day` | number | kilograms per day | Declared outcome 3. Fuelwood used by the household on the monitored day. |
| `respiratory_symptom_score` | integer | none (0 to 12 scale) | Declared outcome 4. Main cook's respiratory symptom questionnaire score; higher means more symptoms. |
| `cooking_time_min` | number | minutes | Declared outcome 5. Total cooking time on the monitored day. |

The five outcome columns appear in the order the study protocol declared them.

## Value ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `kitchen_pm25_ug_m3` | 123.9 | 1215.8 |
| `kitchen_co_ppm` | 1.11 | 28.34 |
| `fuelwood_use_kg_day` | 2.11 | 8.69 |
| `respiratory_symptom_score` | 1 | 11 |
| `cooking_time_min` | 106.9 | 257.9 |

## Provenance

`data.csv` is a fixed authored file. It was written once by `make_data.py` in
this directory, which draws household-level values from the study's realistic
ranges under a fixed random seed. `make_data.py` is a one-time authoring tool and
is not part of the analysis; nothing in the analysis regenerates or simulates
these values.
