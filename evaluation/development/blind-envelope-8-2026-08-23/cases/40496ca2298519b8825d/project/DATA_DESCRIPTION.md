# Data description

Well-nitrate monitoring study comparing agricultural and forested catchments.

Both files were produced by `make_data.py` (Python standard library only, fixed
random seed `20260823`). The values are synthetic but built to the ranges and
structure the study describes. Re-running the script reproduces both files
exactly.

## Units of observation

- **22 wells**, identified `WEL01` through `WEL22`. The well is the independent
  unit: each well is a separate physical monitoring point.
- **6 monthly samples per well**, January through June 2025, giving **132
  samples** in total.

## The two groups

`catchment_type` splits the wells into the two groups being compared. The split
is balanced: **11 wells agricultural, 11 wells forested**. Catchment type is a
property of the well, so it is the same on all six rows for a given well and it
never changes over the monitoring period.

| catchment_type | wells | rows in the raw log |
| --- | --- | --- |
| `agricultural` | 11 | 66 |
| `forested` | 11 | 66 |

## File 1: `nitrate_monitoring_log.csv` (raw monitoring log)

**One row = one water sample: one well on one month.** 132 rows plus a header.
Rows are ordered by well, then by month. The six rows sharing a `well_id` are
repeated measurements at the same well at successive time points, so they are
not independent of one another.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `well_id` | text | — | Well identifier, `WEL01`–`WEL22`. Repeats on 6 rows, once per sampled month. |
| `catchment_type` | text | — | Catchment the well draws from: `agricultural` or `forested`. Fixed per well. |
| `sample_month` | text | — | Month the sample was taken, `YYYY-MM`. One of `2025-01` … `2025-06`. |
| `nitrate_mg_per_l` | number | mg/L | Nitrate concentration measured in that sample. 2 decimal places. Observed range 0.63–10.23. |
| `water_temp_c` | number | °C | Water temperature at the time of sampling. 1 decimal place. Observed range 8.2–15.0. Varies month to month with the season. |
| `well_depth_m` | number | m | Depth of the well. 1 decimal place. Observed range 23.5–95.9. A fixed property of the well, so it repeats unchanged on all six of that well's rows. |

## File 2: `well_nitrate_summary.csv` (per-well summary)

**One row = one well, summarising its whole six-month monitoring period.**
22 rows plus a header, ordered `WEL01` through `WEL22`. This is the
analysis-ready file: it holds exactly one value per well, so its rows are
independent of one another.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `well_id` | text | — | Well identifier, `WEL01`–`WEL22`. Unique; appears on exactly one row. Matches `well_id` in the raw log. |
| `catchment_type` | text | — | Catchment the well draws from: `agricultural` or `forested`. Matches the raw log for the same well. |
| `mean_nitrate_mg_per_l` | number | mg/L | Mean of that well's six monthly `nitrate_mg_per_l` values. 3 decimal places. |
| `n_samples` | integer | count | Number of monthly samples averaged into `mean_nitrate_mg_per_l`. 6 for every well. |

## Relationship between the two files

The summary file is a collapse of the raw log by `well_id`. For every well:

- `mean_nitrate_mg_per_l` is the arithmetic mean of that well's six
  `nitrate_mg_per_l` values as written in the raw file, rounded to 3 decimals.
- `n_samples` is the count of that well's rows in the raw file.
- `catchment_type` agrees with the raw file.

These were checked against the written files: all 22 wells match on all three
counts, every well has exactly 6 raw rows, and `well_depth_m` is constant within
each well.

## Descriptive summary of the outcome

Per-well mean nitrate, from `well_nitrate_summary.csv`:

| catchment_type | wells | mean (mg/L) | SD (mg/L) | min | max |
| --- | --- | --- | --- | --- | --- |
| `agricultural` | 11 | 7.06 | 1.47 | 4.87 | 9.44 |
| `forested` | 11 | 2.42 | 0.63 | 1.67 | 3.42 |

## Missing data

There is none. Every well has all six monthly samples, and no cell in either
file is blank.
