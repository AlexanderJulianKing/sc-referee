# Data description

## Files

### `make_data.py`
Seeded Python generator that writes `fox_habitat_measurements.csv`. It uses a fixed random seed
(`20260824`), so running it again reproduces the same CSV.

### `fox_habitat_measurements.csv`
The field measurement table for the urban/rural red fox comparison. It has a header row and 68 data
rows, one per collared adult fox: 34 trapped in the city and 34 trapped in the surrounding farmland.
Each fox was live-trapped, collared, sampled and released once, and each fox appears exactly once.
Every cell is filled; there are no missing values.

**One row represents one adult red fox**, with its trapping area and the four outcomes measured for
that animal during the study season.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `fox_id` | text | none | Unique animal identifier, `FOX001` through `FOX068`, numbered in trapping order. |
| `habitat_group` | text | none | Trapping area for the animal. Exactly two values appear: `urban` and `rural`. 34 rows each. |
| `body_condition_index` | number | unitless | Mass-for-length body condition score for the animal at capture, recorded to two decimals. Values range from 0.72 to 1.27. |
| `home_range_km2` | number | square kilometres | Home range area estimated from six months of collar fixes, recorded to two decimals. Values range from 0.20 to 22.14. |
| `faecal_cortisol_ng_per_g` | number | nanograms per gram | Faecal cortisol metabolite concentration from the scat sample taken at capture, recorded to one decimal. Values range from 28.8 to 197.9. |
| `diet_shannon_index` | number | unitless | Shannon diversity index of prey and food categories identified in the scat contents, recorded to two decimals. Values range from 0.89 to 2.23. |

#### Note on one home range value
Row `FOX013` (rural) has a home range of 22.14 square kilometres. Every other animal in the table
falls between 0.20 and 4.63 square kilometres. This animal dispersed out of the study area during the
collar period, so its collar fixes cover a far larger area than a resident fox's territory. The value
is kept in the data file as recorded.
