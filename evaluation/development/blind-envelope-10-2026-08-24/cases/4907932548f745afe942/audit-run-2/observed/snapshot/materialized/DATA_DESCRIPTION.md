# Data description

## Files

| File | Role |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (`SEED = 20260124`, NumPy `default_rng`). Running it rewrites `air_quality_winter.csv` with identical contents every time. |
| `air_quality_winter.csv` | The monitoring dataset. 80 data rows plus one header row, comma separated, UTF-8, Unix line endings. |

## What one row represents

One row is one monitoring day at one station: a single complete twenty-four hour
averaging period, at either the kerbside station on the busy arterial road or the urban
background station in the park two kilometres away. The five pollutant columns on that
row are the daily means over that same twenty-four hour period at that same station.

There are 80 rows: 40 kerbside monitoring days (`KRB-001` through `KRB-040`) and 40
background monitoring days (`BGD-001` through `BGD-040`), all from one winter. The two
stations have their own separate sets of monitoring days; a kerbside row and a
background row are not two readings of the same calendar day. Every cell is filled; there
are no blanks and no missing-value codes.

## Columns of `air_quality_winter.csv`

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `day_id` | text | none | Identifier for the monitoring day. Unique across all 80 rows. `KRB-nnn` for kerbside days, `BGD-nnn` for background days. |
| `site_group` | text | none | Station the row comes from. Exactly two values appear: `kerbside` and `background`. 40 rows each. |
| `pm25_ug_m3` | number, 1 decimal | micrograms per cubic metre | Daily mean concentration of fine particulate matter (particles under 2.5 micrometres). Observed range in this file: 6.3 to 32.5. |
| `pm10_ug_m3` | number, 1 decimal | micrograms per cubic metre | Daily mean concentration of coarse-and-fine particulate matter (particles under 10 micrometres). Always at least as large as `pm25_ug_m3` on the same row, because PM2.5 is a subset of PM10. Observed range: 9.0 to 63.2. |
| `no2_ug_m3` | number, 1 decimal | micrograms per cubic metre | Daily mean concentration of nitrogen dioxide. Observed range: 14.3 to 92.0. |
| `o3_ug_m3` | number, 1 decimal | micrograms per cubic metre | Daily mean concentration of ozone. Observed range: 18.0 to 88.4. |
| `black_carbon_ug_m3` | number, 2 decimals | micrograms per cubic metre | Daily mean concentration of black carbon (soot), measured by optical absorption. Observed range: 0.36 to 4.69. |

Column order in the file is exactly the order of the table above.

## Structure the generator builds in

These are properties of how the numbers were produced, recorded here so the shape of the
file is not mysterious.

* Each monitoring day gets one meteorological dispersion factor, standing in for the
  winter weather. High values mean a cold, stagnant, poorly ventilated day on which
  primary pollutants build up; low values mean a windy, well mixed day. That single
  factor feeds every pollutant on the row, so the five pollutant columns are correlated
  within a row rather than independent.
* PM2.5 is mostly regional secondary aerosol that covers the whole city, so the kerbside
  values sit only a little above the background values.
* PM10 adds resuspended road dust and brake and tyre wear at the kerb, so the kerbside
  values sit further above the background values than PM2.5 does.
* NO2 and black carbon are direct traffic exhaust tracers and are markedly higher at the
  kerbside station.
* Ozone is destroyed by fresh nitric oxide from traffic, so kerbside ozone is drawn down
  relative to the regional ozone level of the same kind of day.
* Draws are held inside plausible instrument ranges. Three of the 400 pollutant values in
  the file sit exactly on one of those range limits: one `pm10_ug_m3` at 9.0, one
  `no2_ug_m3` at 92.0, and one `o3_ug_m3` at 18.0.
