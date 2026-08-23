# Data description

## File

`apple_firmness.csv` is the only data file in this project. It holds 1 header row and
128 data rows.

The values are simulated, not measured. `make_data.py` (Python standard library only,
fixed seed `20260822`) writes the file; re-running it reproduces the same CSV.

## What one row is

One row is one individual apple, picked at harvest and tested once with a penetrometer.

## Units in the study

- 16 mature trees of a single cultivar, coded `T-01` through `T-16`.
- Each tree got one of the two irrigation schedules for the eight weeks before harvest:
  8 trees on `standard`, 8 on `deficit`.
- 8 fruit were picked from around the canopy of each tree, so each tree contributes
  8 rows: 16 trees x 8 fruit = 128 rows.
- Fruit per schedule: 64 `standard`, 64 `deficit`.

## The two groups

| irrigation | trees | fruit (rows) | tree codes |
| --- | --- | --- | --- |
| standard | 8 | 64 | T-01, T-03, T-05, T-06, T-08, T-09, T-15, T-16 |
| deficit | 8 | 64 | T-02, T-04, T-07, T-10, T-11, T-12, T-13, T-14 |

## Columns, in file order

| # | Column | Type | Values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `tree_code` | text | `T-01` ... `T-16` | Identifier of the tree the fruit was picked from. Appears 8 times, once per fruit from that tree. |
| 2 | `irrigation` | text | `standard`, `deficit` | Summer irrigation schedule applied to that tree for the eight weeks before harvest. Constant within a tree. |
| 3 | `fruit_position` | integer | 1 ... 8 | Label for the sampling slot around the canopy for that fruit within its tree. It numbers the 8 fruit taken from one tree; it is not a physical measurement and carries no order across trees. |
| 4 | `firmness_N` | number, 1 decimal | 54.4 to 77.7 in this file | Flesh firmness of that single fruit in newtons, from the penetrometer. |

## How the values were generated

Firmness was drawn in two stages, matching the magnitudes given for the study:

1. Each tree got its own mean: the group mean (63.0 N for `standard`, 68.0 N for
   `deficit`) plus a tree offset drawn from a normal distribution with SD 3.0 N,
   standing in for crop load and canopy position.
2. Each fruit was drawn from a normal distribution around its own tree's mean with
   SD 4.0 N.

Draws outside 50.0 to 82.0 N were redrawn, so every recorded value sits inside the
plausible penetrometer range. Values are rounded to one decimal place.

Realized figures in the delivered file: mean firmness 62.36 N (SD 5.54) for `standard`
and 68.51 N (SD 3.81) for `deficit`; overall range 54.4 to 77.7 N.
