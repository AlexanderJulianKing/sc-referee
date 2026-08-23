# Data description

## File

`coffee_stomatal_conductance.csv` — one comma-separated table, 1 header line plus 120 data rows.

## What one row represents

One row is **one measured leaf**: a single porometer reading taken on one fully expanded leaf of one
coffee shrub on a single clear morning. A row is not a shrub and not a treatment group.

## Units of observation

- **20 shrubs.** Mature arabica coffee of the same variety and age, all on one estate.
- **6 leaves per shrub.** Six fully expanded leaves were chosen on each shrub and spread around the
  canopy, and each leaf was measured individually.
- **120 rows.** 20 shrubs x 6 leaves = 120 measured leaves, one row each.

The six rows that share a `shrub_label` are six leaves from that same shrub. Rows are therefore
grouped inside shrubs: leaves are nested within shrubs, and shrubs are nested within treatment.

## The two groups

The grouping variable is `canopy_treatment`, with two levels:

| Level | Meaning | Shrubs | Rows (leaves) |
|---|---|---|---|
| `shade_trees` | Shrub grows under a canopy of nitrogen-fixing shade trees | 10 | 60 |
| `full_sun` | Shrub grows in full sun, with no overhead canopy | 10 | 60 |

The groups are balanced: 10 shrubs and 60 leaves each.

## Columns

Columns appear in the file in this order.

| # | Column | Type | Units | Description |
|---|---|---|---|---|
| 1 | `shrub_label` | text | none | Field tag of the shrub the leaf came from, formatted `Rnn-Pnn`: the estate row number (`R`) and the shrub's position along that row (`P`). Example: `R02-P03`. 20 distinct values, each appearing on exactly 6 rows. |
| 2 | `canopy_treatment` | text (2 levels) | none | Growing condition of the shrub: `shade_trees` or `full_sun`. Constant across all 6 rows of a given shrub, because the treatment is a property of the shrub, not of the leaf. |
| 3 | `leaf_position` | text (6 levels) | none | Where on the shrub's canopy the measured leaf sat: `upper_north`, `upper_south`, `mid_east`, `mid_west`, `lower_east`, `lower_west`. Height band (upper / mid / lower) plus aspect. Each of the six values appears exactly once per shrub. |
| 4 | `leaf_temp_c` | number, 1 decimal | degrees Celsius | Temperature of that leaf at the moment of measurement. Observed range 24.0 to 32.4. |
| 5 | `stomatal_conductance_mmol_m2_s` | integer | mmol H2O m-2 s-1 | The outcome. Stomatal conductance to water vapour for that leaf, from the porometer, rounded to a whole number. Observed range 110 to 300. |

## Observed values by group

| Group | Leaves | Conductance mean | Conductance SD | Conductance range | Leaf temp mean | Leaf temp range |
|---|---|---|---|---|---|---|
| `full_sun` | 60 | 154.8 | 20.1 | 110 to 203 | 29.7 | 26.6 to 32.4 |
| `shade_trees` | 60 | 228.5 | 23.9 | 178 to 300 | 26.1 | 24.0 to 29.2 |

Spread comes from two sources: shrubs differ from one another (rooting depth and crop load), and
leaves on the same shrub differ from one another.

## Completeness and provenance

There are no missing values, no blank cells, and no duplicate leaf records. Every shrub contributes
all 6 leaves.

The values are simulated, not measured in the field. They were produced by `make_data.py` in this
directory using only the Python standard library with the fixed seed `20260822`, so re-running that
script reproduces the file exactly.
