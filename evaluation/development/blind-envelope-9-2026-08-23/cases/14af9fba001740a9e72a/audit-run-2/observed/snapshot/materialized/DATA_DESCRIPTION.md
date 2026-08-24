# Data description

## The file

`hop_cone_alpha_acids.csv` — one CSV, 120 data rows plus one header row, 4 columns.

It is the only data file in the project. It was produced by `make_data.py` (Python standard
library only, fixed random seed), so re-running that script rewrites the same table.

## What one row is

One row is **one hop cone**: a single cone picked from a single bine and assayed on its own for
alpha-acid content.

A row is not a bine. Each bine appears on six rows, once for each of the six cones picked from
it at harvest.

## How many units and how many rows

- 20 bines (the units that received a nitrogen rate), tagged `BINE-01` through `BINE-20`.
- 6 cones assayed per bine.
- 20 x 6 = **120 rows**, evenly balanced: every bine has exactly six rows, no missing cones.

## The two groups

The nitrogen top-dressing rate was set per bine, so all six rows from a bine carry the same
rate.

| `nitrogen_rate` | Meaning | Bines | Rows |
| --- | --- | --- | --- |
| `standard` | The farm's standard nitrogen top-dressing rate | 10 | 60 |
| `reduced` | The reduced top-dressing rate under test | 10 | 60 |

Rates alternate down the tag order (odd-numbered tags standard, even-numbered tags reduced), so
neither treatment sits entirely at one end of the trellis row.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `bine_tag` | text | The numbered aluminium tag fixed to the bine the cone came from, formatted `BINE-01` … `BINE-20`. Identifies the unit. Repeats on six rows. |
| `nitrogen_rate` | text | Nitrogen top-dressing rate applied to that bine: `standard` or `reduced`. Constant within a bine. |
| `cone_number` | integer | Which of the six cones from that bine this row is, 1–6. It is a label for the cone within its bine, not an ordering across bines and not a time or dose. |
| `alpha_acid_percent` | number | Alpha-acid content of that one cone, as a percentage of dry cone weight, reported to two decimal places. This is the measured outcome. |

## Values in the generated table

| Quantity | Value |
| --- | --- |
| Range of `alpha_acid_percent` | 8.51 to 13.69 percent |
| Mean, `standard` bines | 11.46 percent |
| Mean, `reduced` bines | 10.66 percent |
| Difference in group means | 0.80 percentage points lower under the reduced rate |
| Spread of the 20 bine means (standard deviation) | 1.23 percentage points |
| Typical cone-to-cone spread within one bine (mean of the 20 within-bine standard deviations) | 0.52 percentage points |

The generator builds each value in two layers, matching how the measurements arise in the field:
one offset drawn per bine (standard deviation 1.1 percentage points) for everything that makes
one bine differ from another, plus one residual drawn per cone (standard deviation 0.6
percentage points) for cone-to-cone variation and assay error. Because of that layering, six
cones from the same bine resemble each other more closely than cones taken from different bines.
