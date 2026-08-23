# Data description

Two CSV files describe one irrigated rice trial that compared two nitrogen top-dressing
schedules. Both files were produced by `make_data.py` (Python standard library only,
fixed random seed `20260841`), so they are simulated values chosen to look like a real
station record. Re-running the script reproduces both files exactly.

## Design

- 18 bunded paddies, coded `P-01` through `P-18`. One paddy is one experimental unit.
- Two groups, 9 paddies each:
  - `split` — nitrogen top-dressing applied in split doses.
  - `late` — a single late nitrogen top-dressing.
  - The two labels are interleaved across the paddy numbering, so the schedule is not
    tied to the order in which paddies are coded.
- At harvest, 6 hills were cut from marked positions inside each paddy and threshed
  separately. Those 6 hills are spatial subsamples within a paddy, not independent
  units, so 18 paddies x 6 hills = 108 hill records.

## File 1: `hill_harvest_raw.csv`

The raw field record. **One row is one harvested hill.** 108 data rows plus a header row.

| Column | Type | Meaning |
| --- | --- | --- |
| `paddy_code` | text | Paddy the hill came from, `P-01` to `P-18`. 18 distinct values, 6 rows each. |
| `nitrogen_schedule` | text | Nitrogen schedule for that paddy: `split` or `late`. Constant within a paddy. 54 rows per schedule. |
| `hill_position` | integer | Marked sampling position inside the paddy, 1 to 6. Each position appears once per paddy. |
| `hill_grain_yield_g` | number, 1 decimal | Threshed grain yield of that single hill, in grams. |

Observed range of `hill_grain_yield_g`: 28.3 g to 62.8 g. Mean spread of hills inside a
single paddy is about 5.1 g (standard deviation), matching the intended within-paddy
field variability.

## File 2: `paddy_harvest_summary.csv`

The station's per-paddy harvest summary, prepared by the field team before analysis.
**One row is one paddy.** 18 data rows plus a header row.

| Column | Type | Meaning |
| --- | --- | --- |
| `paddy_code` | text | Paddy identifier, `P-01` to `P-18`. Unique in this file, and matches File 1. |
| `nitrogen_schedule` | text | Nitrogen schedule for that paddy: `split` or `late`. 9 rows per schedule. |
| `hills_sampled` | integer | Number of hills harvested from that paddy. 6 for every paddy. |
| `mean_hill_yield_g` | number, 1 decimal | Mean grain yield per hill for that paddy, in grams. |

## How the two files line up

`mean_hill_yield_g` for a paddy equals the mean of that paddy's 6 `hill_grain_yield_g`
values in File 1, rounded to one decimal place. This was checked for all 18 paddies.
`nitrogen_schedule` also agrees between the two files for every paddy, and
`hills_sampled` is 6 for every paddy, which agrees with the 6 rows per paddy in File 1.

## Group summary (from `paddy_harvest_summary.csv`)

| Schedule | Paddies | Mean of `mean_hill_yield_g` | SD across paddies |
| --- | --- | --- | --- |
| `split` | 9 | 41.8 g | 2.3 g |
| `late` | 9 | 47.1 g | 5.9 g |

These group numbers are given here only to describe the data files. No test has been
run yet.
