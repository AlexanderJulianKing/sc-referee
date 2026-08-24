# Data description

## File

`erg_trials.csv` is the only data file in this project. It holds the maximal 500 metre
ergometer trials recorded after the two six-week training blocks.

`make_data.py` is the generator that produced it (Python standard library only, fixed
seed `20260217`). Re-running `python3 make_data.py` rewrites the same CSV.

## What one row represents

One row is **one 500 metre ergometer trial by one rower on one day**. It is a single
performance, not a rower average and not a training block summary.

## Units and counts

- 18 rowers, identified `R01` through `R18`.
- 2 training blocks, 9 rowers in each: `interval` (high-intensity interval block) and
  `endurance` (steady-state endurance block).
- 4 trials per rower, each on a separate day under the same conditions.
- 72 rows in total (18 rowers x 4 trials), plus one header line.
- Rows are ordered by rower, and within a rower by trial number.
- No missing values; every rower has all four trials.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `rower_id` | text | Athlete code for the rower who performed the trial, `R01` to `R18`. This is the unit column: four rows share each code. |
| `training_block` | text | Which six-week block that rower completed, either `interval` or `endurance`. It is fixed for a rower, so all four of a rower's rows carry the same value. |
| `trial_number` | integer | Which trial this is for that rower, 1 to 4, one per test day. |
| `mean_power_w` | number | Mean power output over the 500 metre trial, in watts, recorded to one decimal place. This is the outcome. |

## The two groups

| Group | Rowers | Rows | Mean power (W) |
| --- | --- | --- | --- |
| `interval` | 9 | 36 | 282.4 |
| `endurance` | 9 | 36 | 266.8 |

## Spread in the recorded values

- Values run from 231.1 W to 322.1 W, with an overall mean of 274.6 W.
- The four trials by one rower sit close together: the average standard deviation within
  a rower is about 6 W.
- Different rowers sit much further apart: the standard deviation of the 18 rower means
  is about 23 W.

That contrast is a property of the data itself. The four rows belonging to one rower are
repeated measurements of the same athlete, so they carry less new information than four
rows from four different athletes would.
