# Data description

## Files

### `make_data.py`

The generator that produced the data file. It uses one fixed random seed, so running it
again rewrites `pepper_lighting_trial.csv` with exactly the same values.

### `pepper_lighting_trial.csv`

The trial data table. It has a header row and 36 data rows, one for each plant in the
supplemental-lighting trial on winter glasshouse sweet peppers.

**One row is one pepper plant**: a single pot on the bench, recorded once at the end of the
season. The plant was picked many times over the winter, and the numbers in its row are that
plant's season totals or season averages, not the record of a single picking day. There are
18 plants under each of the two lighting spectra, and every plant has a value in every
column, so the table has no blanks.

## Columns

Columns appear in this order: the plant identifier, the lighting treatment, and then the
seven trial outcomes in the order the protocol declared them.

| # | Column | What it holds | Unit |
|---|--------|---------------|------|
| 1 | `plant_id` | Label for the individual plant. `W01`–`W18` are the broad white plants, `R01`–`R18` the red and blue plants. Each label appears once. | none (text) |
| 2 | `group` | The supplemental lighting spectrum the plant grew under. Exactly two entries occur: `broad_white` for the broad white LED module and `red_blue` for the red and blue module. | none (text) |
| 3 | `yield_kg` | Total marketable fruit yield harvested from the plant across the whole season. | kilograms per plant |
| 4 | `fruit_mass_g` | Mean fresh mass of one marketable fruit from that plant, over all its marketable fruit. | grams |
| 5 | `wall_thickness_mm` | Fruit wall (pericarp) thickness for the plant, averaged over three fruit taken from it. | millimetres |
| 6 | `brix` | Soluble solids content of the plant's fruit. | degrees Brix |
| 7 | `ascorbic_mg_100g` | Ascorbic acid (vitamin C) content of the plant's fruit. | milligrams per 100 grams fresh weight |
| 8 | `leaf_area_m2` | Total leaf area of the plant, measured at the final harvest. | square metres per plant |
| 9 | `days_to_harvest` | Time from transplanting to the plant's first marketable harvest. Whole days. | days |

## Values in the file

All numbers are plant-level records with realistic plant-to-plant spread. The observed
ranges in this file are:

| Column | Minimum | Maximum |
|--------|---------|---------|
| `yield_kg` | 2.05 | 4.11 |
| `fruit_mass_g` | 135.1 | 214.4 |
| `wall_thickness_mm` | 4.7 | 8.7 |
| `brix` | 6.0 | 8.4 |
| `ascorbic_mg_100g` | 95.9 | 165.3 |
| `leaf_area_m2` | 0.405 | 0.965 |
| `days_to_harvest` | 64 | 83 |

Two plants in each group (`W04`, `W15`, `R07`, `R12`) established slowly in the pot and ran
weak all season. They carry lower yield, smaller leaf area and a later first harvest than
their bench mates. They are ordinary trial plants, not errors, and they are recorded the
same way as every other plant.

`yield_kg` is written with two decimal places; `fruit_mass_g`, `wall_thickness_mm`, `brix`
and `ascorbic_mg_100g` with one; `leaf_area_m2` with three; `days_to_harvest` as an integer.
