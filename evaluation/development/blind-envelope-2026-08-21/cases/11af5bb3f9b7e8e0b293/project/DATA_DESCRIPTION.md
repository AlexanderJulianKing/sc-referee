# Data description

The file `nubbin_calcification.csv` holds the calcification measurements from the
*Acropora millepora* thermal-stress experiment.

## What one row is

One row is one nubbin: a single coral fragment cut from a parent colony, held for
8 weeks in its colony's assigned thermal regime, and weighed by buoyant weight at
the start and the end. Every row is one measured fragment, not one colony.

Five rows share each parent colony, because five nubbins were cut from each
colony. Those five fragments are clones of one another, so rows that share a
`parent_colony` value are not independent observations.

## How many units and how many rows

- 14 parent colonies. These are the wild colonies that were collected, and they
  are the units that were assigned to a thermal regime.
- 5 nubbins per parent colony.
- 70 data rows (14 x 5), plus one header row, so the file has 71 lines.

## The two groups

The thermal regime was assigned to a whole parent colony, so all five nubbins from
a colony sit in the same group. There are two groups, 7 colonies each:

| Group | Temperature | Parent colonies | Nubbin rows |
|---|---|---|---|
| `ambient` | 27 degrees C | COL-A, COL-C, COL-E, COL-G, COL-I, COL-K, COL-M | 35 |
| `heated` | 29 degrees C | COL-B, COL-D, COL-F, COL-H, COL-J, COL-L, COL-N | 35 |

## Columns

| Column | Type | Description |
|---|---|---|
| `parent_colony` | string | Label of the wild colony the nubbin was cut from, `COL-A` through `COL-N`. Fourteen distinct values, each appearing in 5 rows. This is the grouping variable for the shared genotype. |
| `thermal_regime` | string | The temperature treatment the nubbin experienced, either `ambient` (27 degrees C) or `heated` (29 degrees C). Constant within a parent colony, because assignment was done at the colony level. |
| `nubbin_code` | string | Identifier of the nubbin within its parent colony, `n1` through `n5`. It is unique only inside a colony, so a nubbin is identified by the pair (`parent_colony`, `nubbin_code`). |
| `initial_weight_g` | number, 2 decimals | Buoyant weight of the nubbin in grams at the start of the 8-week run. Values run from 4.50 to 11.96 g. |
| `calcification_rate` | number, 3 decimals | The outcome. Net calcification over the 8 weeks, in milligrams of calcium carbonate per gram of skeleton per day. Values run from 0.504 to 1.453 mg g^-1 day^-1. |

Rows are ordered colony by colony (COL-A first through COL-N last), and within a
colony by nubbin code n1 through n5.

## How the file was made

`make_data.py` generates the file with a fixed random seed (20261187), so re-running
it reproduces the same 70 rows byte for byte. Each parent colony was given its own
baseline calcification rate, and the five nubbins from that colony vary only
slightly around it. The spread of the colony baselines is larger than the average
gap between the two thermal regimes, which is why the genotype grouping matters for
any analysis of this file.
