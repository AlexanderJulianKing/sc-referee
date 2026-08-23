# Data description

## File

`sleep_efficiency.csv` — the single data file for this project. It is simulated, not
collected from real people. It is produced by `make_data.py` (Python standard library only,
fixed seed `20260881`), so rerunning that script rewrites the identical file.

The study asks whether sleep quality differs between two shift-rotation patterns at a large
distribution warehouse. Twenty-six workers wore wrist actigraphy monitors for seven
consecutive nights each.

## What one row is

One row is **one monitored night for one worker**. It is not one worker and not one shift.
Because each worker contributes seven rows, the seven rows sharing a `worker_id` are seven
nights of sleep from the same person, so they are repeated measurements rather than
measurements from seven different people.

## Units and counts

| Quantity | Count |
| --- | --- |
| Workers (people monitored) | 26 |
| Nights monitored per worker | 7 |
| Data rows in the CSV | 182 |
| Lines in the file including the header row | 183 |
| Workers on the slow rotation | 13 |
| Workers on the rapid rotation | 13 |
| Rows from slow-rotation workers | 91 |
| Rows from rapid-rotation workers | 91 |

Every worker has a complete set of seven nights. There are no missing values and no blank
cells.

## The two groups

`rotation_pattern` splits the workers into the two shift patterns being compared:

- **`slow`** — a slowly rotating shift pattern. Workers `WK-01` through `WK-13`.
- **`rapid`** — a rapidly rotating shift pattern. Workers `WK-14` through `WK-26`.

Each worker belongs to exactly one pattern for all seven of their nights. The pattern never
changes within a worker, so `rotation_pattern` is a property of the person, not of the night.

## Columns

The file has four columns, in this order.

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `worker_id` | text | `WK-01` … `WK-26` (26 distinct values) | Identifier of the worker who was monitored. Appears on exactly 7 rows, one per night. This is the column that links repeated nights back to one person. |
| 2 | `rotation_pattern` | text | `slow` or `rapid` | Which shift-rotation pattern that worker was on. Constant across a worker's 7 rows. This is the grouping variable for the comparison. |
| 3 | `night_number` | integer | 1 … 7 | Which of the seven consecutive monitored nights this row is, counted within the worker. Night 1 for one worker is not necessarily the same calendar date as night 1 for another. |
| 4 | `sleep_efficiency_pct` | number, one decimal place | 61.7 … 99.0 in this file; held by construction inside 55.0–99.0 | The outcome. Sleep efficiency is the percentage of the time spent in bed that was actually spent asleep, as scored by the wrist actigraphy monitor for that night. Higher is better sleep. |

## How the values were simulated

`make_data.py` builds each value in two layers, which is what makes the nights within a
worker resemble each other more than nights from different workers:

1. **A personal usual level for each worker**, drawn around that worker's rotation-pattern
   mean, with a between-worker standard deviation of 4.0 percentage points. The pattern means
   used are 84.5 percent for `slow` and 78.9 percent for `rapid`.
2. **A nightly wobble around that worker's own usual level**, with a within-worker standard
   deviation of 5.0 percentage points.

Each result is then rounded to one decimal place and clipped into the 55.0–99.0 percent range
that actigraphy sleep efficiency plausibly occupies. Three of the 182 values in this file sit
exactly on the 99.0 ceiling because of that clipping.

Because the between-worker layer is applied once per person and then shared by all seven of
that person's nights, the 182 rows are not 182 independent observations. They carry
information about 26 people.
