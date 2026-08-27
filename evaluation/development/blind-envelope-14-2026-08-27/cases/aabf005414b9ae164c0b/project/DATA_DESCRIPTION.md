# Data description

File: `radon_mitigation_survey.csv` (header row plus 56 data rows, comma separated, no
missing cells).

**One row = one single-family house** in the mitigation survey. Each house was fitted
with one mitigation system, then surveyed once over a single ninety-day measurement
period twelve months after installation. The four outcome columns are the values from
that one survey of that one house, so a house appears exactly once.

All fifty-six houses sit on the same permeable gravel subsoil and all had confirmed
elevated indoor radon before installation. Twenty-eight houses are in each mitigation
group.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `house_id` | text | none | House identifier, `H-001` through `H-056`. Unique across the file. |
| `mitigation` | text | none | Mitigation system installed. Exactly two values: `active_subslab` (active sub-slab depressurisation fan system, 28 houses) and `passive_stack` (enhanced passive stack with sealed floor penetrations, 28 houses). |
| `living_room_radon_bq_per_m3` | integer | Bq/m3 | Declared outcome 1. Living room radon concentration over the ninety-day period, rounded to whole becquerels per cubic metre. |
| `bedroom_radon_bq_per_m3` | integer | Bq/m3 | Declared outcome 2. Main bedroom radon concentration over the same period, rounded to whole becquerels per cubic metre. |
| `air_change_rate_ach` | decimal | air changes per hour | Declared outcome 3. Whole-house air change rate, rounded to two decimals. |
| `indoor_rh_pct` | decimal | percent | Declared outcome 4. Mean indoor relative humidity over the measurement period, rounded to one decimal. |

The four outcome columns appear in the order the service declared them before
installation: living room radon, bedroom radon, air change rate, indoor relative
humidity.

## Observed ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `living_room_radon_bq_per_m3` | 51 | 280 |
| `bedroom_radon_bq_per_m3` | 43 | 207 |
| `air_change_rate_ach` | 0.23 | 1.03 |
| `indoor_rh_pct` | 34.7 | 57.7 |

Both radon columns are right-skewed, as radon survey data usually is, and the two
rooms in the same house move together (a leaky house reads high in both rooms).
