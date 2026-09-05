# Data description

`data.csv` holds the end-of-study measurements from the winter food supplementation
experiment on wild-caught bank voles.

**One row is one vole.** Each animal was held singly for four weeks in its own outdoor
pen of identical construction on the same site, measured once at the end of the four
weeks, and then released. There are 48 rows, one per animal, plus a single header row.
There are no repeated rows, no summary rows, and no empty cells: every vole has a value
in every column.

Twenty-four voles are in the supplemented group (a daily supplement of seed and grain)
and twenty-four are in the unsupplemented group (no supplement). Pens were otherwise
identical in shelter and natural vegetation.

## Columns

The columns appear in this order.

| Column | Meaning | Unit / values |
| --- | --- | --- |
| `vole_id` | Animal identifier, one per vole, `vole_01` through `vole_48` | text label, no unit |
| `supplement_group` | Which feeding treatment the vole's pen received | text, either `supplemented` or `unsupplemented` |
| `mass_change_g` | Change in body mass over the four weeks (end mass minus start mass); negative values are animals that lost mass | grams (g), recorded to 0.1 g |
| `resting_metabolic_rate_ml_o2_per_h` | Resting metabolic rate measured by respirometry at the end of the four weeks | millilitres of oxygen per hour (ml O2/h), recorded to 0.1 |
| `faecal_corticosterone_ng_per_g` | Concentration of faecal corticosterone metabolites | nanograms per gram of dry faeces (ng/g), recorded as whole numbers |
| `distance_moved_per_night_m` | Distance moved per night inside the pen, from radio tracking | metres (m), recorded as whole numbers |

The four measurement columns are the study's declared outcomes and appear in the order
they were declared in the licence application and study protocol: body mass change,
resting metabolic rate, faecal corticosterone metabolites, then distance moved per night.

`data.csv` is a fixed data file. It is read as it stands and is never regenerated,
simulated, or overwritten by the analysis.
