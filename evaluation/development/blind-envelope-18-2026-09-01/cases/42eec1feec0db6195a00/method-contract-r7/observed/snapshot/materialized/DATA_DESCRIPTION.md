# Data description: `data.csv`

Street tree monitoring of 60 young small-leaved lime trees planted three years ago in tree pits
along comparable inner-city streets. Thirty trees were planted into pits filled with an engineered
structural pit soil and thirty into pits filled with the standard site backfill. Every tree was
measured once, at the end of the same growing season, by the same surveying crew.

## What one row represents

One row is one tree: the single end-of-season measurement set for that tree, together with its
identifier and the pit soil type it was planted into. There are 60 data rows plus a header row, and
each tree appears exactly once. There are no blank cells.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `tree_id` | text | none | Tree identifier, `T001` through `T060`, unique to one tree. Follows the crew's survey order. |
| `pit_soil_type` | text | none | Pit soil the tree was planted into. Exactly two values: `engineered_structural_soil` (30 trees) and `standard_backfill` (30 trees). This is the group column. |
| `trunk_diameter_increment_mm` | number | millimetres (mm) | Declared outcome 1. Trunk diameter increment over the growing season. Values in the file run from 7.0 to 15.9, recorded to one decimal place. |
| `canopy_area_m2` | number | square metres (m2) | Declared outcome 2. Projected canopy area. Values in the file run from 4.88 to 10.88, recorded to two decimal places. |
| `leaf_chlorophyll_index` | number | none (relative units of a handheld leaf meter) | Declared outcome 3. Leaf chlorophyll index. Values in the file run from 30.0 to 43.7, recorded to one decimal place. The reading is an index in the meter's own relative units, so the column name carries no unit abbreviation. |
| `midday_stem_water_potential_mpa` | number | megapascals (MPa) | Declared outcome 4. Midday stem water potential. This quantity is negative; values in the file run from -1.67 to -0.95, recorded to two decimal places. |

The four outcome columns appear in the order the monitoring plan declared them. There are no other
measurement columns.
