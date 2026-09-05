# Data description

File: `cyclamen_substrate_trial.csv`

One row is one pot-grown cyclamen plant, assessed once, fourteen weeks after potting.
The file has a header row and 80 data rows: 80 rooted young plants of a single cultivar,
potted on the same day into identical 12 cm pots, randomised across one glasshouse bench
block, with the same irrigation, feeding, light, and temperature for every plant.
Forty plants are in each substrate group, and every plant has a value for every outcome
(no blank cells).

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `plant_id` | text | Plant identifier, `P001` through `P080`. One identifier per plant, all unique. |
| `substrate` | text | Growing substrate group. Exactly two values: `peat_based` (conventional peat-based substrate, 40 plants) and `peat_free` (blend of coir and wood fibre, 40 plants). |
| `canopy_diameter_cm` | number (1 decimal) | Declared outcome 1. Plant canopy diameter in centimetres at fourteen weeks. |
| `open_flower_count` | whole number | Declared outcome 2. Number of fully open flowers on the plant at fourteen weeks. |
| `shoot_dry_mass_g` | number (2 decimals) | Declared outcome 3. Shoot dry mass in grams. |
| `spad_reading` | number (1 decimal) | Declared outcome 4. Leaf chlorophyll meter reading in SPAD units. |
| `days_to_first_flower` | whole number | Declared outcome 5. Days from potting to the first fully open flower. |

The five outcome columns appear in the order the unit declared them before potting.

## Observed value ranges

| Column | Minimum | Maximum |
| --- | --- | --- |
| `canopy_diameter_cm` | 18.1 | 32.2 |
| `open_flower_count` | 3 | 24 |
| `shoot_dry_mass_g` | 5.50 | 20.12 |
| `spad_reading` | 33.8 | 62.0 |
| `days_to_first_flower` | 58 | 94 |

## How the file was produced

The values are invented for this exercise, not measured. A generator script
(`make_data.py`, kept alongside the CSV in staging) draws each plant's five outcomes from
normal distributions with a shared per-plant vigour term, so the outcomes stay correlated
within a plant the way real glasshouse measurements are. Group means, spreads, and the
size of each group offset were fixed by design before the draw, and values are clipped to
the plausible ranges given for each outcome. The generator uses a fixed seed
(`20260826`), so the file reproduces exactly.
