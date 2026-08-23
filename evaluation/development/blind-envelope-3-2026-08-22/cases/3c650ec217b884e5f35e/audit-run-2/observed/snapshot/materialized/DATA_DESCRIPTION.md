# Data description

## The file

There is one data file, `strawberry_brix.csv`. It holds 144 data rows plus a single header
row, and it is comma separated with lowercase underscore-joined column names.

The values are invented rather than measured. They were produced by `make_data.py`
(standard library only, fixed seed `20260822`), which can be re-run to reproduce the file
byte for byte.

## What one row represents

**One row is one berry.** Each row records a single ripe berry picked from a single mother
plant, together with the identity, irrigation schedule, and polytunnel row of the plant it
came from.

Rows are therefore not independent of one another. Six rows share each mother plant, and
those six berries carry that plant's growing conditions, root zone, and genetics in common.
The plant is the unit that was assigned to an irrigation schedule; the berry is only a
subsample taken from it. Any comparison of the two schedules has to be made on one value per
plant, not on the 144 berry rows, or the sample size will be overstated by a factor of six.

## Units and counts

| Level | Count |
|---|---|
| Mother plants (experimental units) | 24 |
| Berries per plant (subsamples) | 6 |
| Berry rows in the file | 144 |
| Polytunnel rows | 4, holding 6 plants each |

## The two groups

The 24 mother plants were split evenly between two irrigation schedules, 12 plants each:

- **`deficit`** — the deficit irrigation schedule, 12 plants, 72 berry rows.
- **`full`** — the standard full irrigation schedule, 12 plants, 72 berry rows.

Schedule is a property of the plant, not of the berry: all six berries from a given plant
carry the same schedule label. The two schedules are balanced across the polytunnel, with
three deficit and three full plants in each of the four rows, so schedule is not confounded
with position in the tunnel.

## Columns

| Column | Type | Description |
|---|---|---|
| `plant_id` | text | Identifier of the mother plant the berry was picked from, `P01` through `P24`. This is the experimental unit. Each value appears in exactly 6 rows. |
| `irrigation_schedule` | text | Irrigation treatment applied to that plant, either `deficit` or `full`. Constant within a plant. |
| `berry_id` | text | Identifier of the individual berry, formed as the plant identifier followed by the berry number within that plant, for example `P01_B3`. Unique across all 144 rows. |
| `soluble_solids_brix` | number | Soluble solids content of that berry in degrees Brix, read on a hand refractometer and recorded to 0.1. This is the response variable. Observed range 5.4 to 10.3. |
| `berry_fresh_weight_g` | number | Fresh weight of that berry in grams, recorded to 0.1 on a bench balance. Observed range 11.2 to 25.1, averaging 18.1. |
| `polytunnel_row` | integer | Row of the polytunnel the plant sat in, 1 to 4. A property of the plant, constant within a plant. |

## How the values were generated

Soluble solids were built as a nested draw: each plant received its own offset around its
schedule mean, and each of its six berries then varied around that plant's level. The
generator used schedule means of 8.6 degrees Brix under deficit irrigation and 7.5 under
full irrigation, a between-plant standard deviation of 0.6, and a within-plant
berry-to-berry standard deviation of 0.9. Berry fresh weight was generated the same way,
centred near 18 g overall and set a little lower under deficit irrigation, which is the
usual direction for restricted water.

Draws falling outside the plausible reading range for ripe fruit (5.0 to 13.0 degrees Brix,
6 to 35 g) were redrawn rather than trimmed to the boundary, so no values pile up at the
limits. Both limits sit more than two standard deviations from their group means, so
redrawing was rare and the target spreads are essentially unchanged.

Because the 12 plants per group are a finite sample, the realised summaries differ a little
from those targets, as real data would. The realised per-plant mean soluble solids are 8.38
degrees Brix for deficit and 7.60 for full, with between-plant standard deviations of 0.43
and 0.83 and a mean within-plant standard deviation of 0.74 and 0.87.

## Note on scope

There is only this one data file. No per-plant summary file is distributed with the data:
the reduction from 144 berry rows to 24 per-plant values is a step of the analysis and is
carried out in `analysis.py`.
