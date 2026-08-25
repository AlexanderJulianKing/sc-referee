# Data description

Dual-purpose industrial hemp, one cultivar, one field site. Ninety-six individually tagged plants
were processed, 48 harvested at early flowering and 48 harvested at seed maturity. Each plant was
measured once, after retting and decortication.

## Files

### `hemp_harvest_timing.csv`

The analysis input. 96 data rows plus one header row. **One row is one tagged plant**, carrying that
plant's harvest timing and its single measured value for each of the five declared outcomes. No cell
is empty.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `plant_id` | text | none | Tag identifier for the plant, `HMP-001` through `HMP-096`. Unique across the file. |
| `harvest_group` | text | none | Harvest timing the plant was assigned to. Exactly two values: `early_flower` (harvest at early flowering) and `seed_mature` (harvest at seed maturity). 48 plants each. |
| `bast_fibre_yield_g` | number | grams per plant | Dry bast fibre recovered from the plant after retting and decortication. Recorded to 0.1 g. |
| `tensile_strength_mpa` | number | megapascals | Tensile strength of the plant's fibre bundle. Recorded to the nearest 1 MPa. |
| `stem_diameter_mm` | number | millimetres | Stem diameter at mid height. Recorded to 0.1 mm. |
| `cbd_pct_dry` | number | percent | Cannabidiol content as a percent of dry inflorescence mass. Recorded to 0.01 percent. |
| `stem_moisture_pct` | number | percent | Stem moisture at harvest, as a percent of fresh stem mass. Recorded to 0.1 percent. |

Observed ranges in the file: bast fibre yield 29.3 to 76.7 g, tensile strength 374 to 863 MPa, stem
diameter 6.0 to 13.8 mm, CBD 0.40 to 2.36 percent, stem moisture 8.0 to 24.4 percent.

### `make_data.py`

The generator that produced `hemp_harvest_timing.csv`. It draws each outcome from a normal
distribution with group-specific mean and spread, adds a shared plant-level vigour term so that the
size-related traits co-vary within a plant, clips each draw to the agronomically plausible range for
that outcome, and rounds to the recording precision listed above. The random seed is fixed at
`20260824` inside the script, so re-running it reproduces the same CSV.

Run it with:

```
python make_data.py
```
