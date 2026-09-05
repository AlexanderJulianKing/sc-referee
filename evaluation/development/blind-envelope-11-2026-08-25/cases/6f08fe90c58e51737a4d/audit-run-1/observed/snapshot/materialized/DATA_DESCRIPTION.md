# Data description

Black soldier fly substrate feed trial, production unit records.

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (`SEED = 2125`, Python standard library only). Running it writes `bsf_substrate_trial.csv` in the same directory. Re-running it reproduces the file byte for byte. |
| `bsf_substrate_trial.csv` | The study data. 48 data rows plus one header row, UTF-8, comma separated, no missing cells. |

## `bsf_substrate_trial.csv`

**One row is one rearing crate.** All 48 crates were identical, were seeded with the same number
of neonate larvae on the same day, and were harvested when the first prepupae appeared in that
crate. Each row therefore carries the substrate that crate was fed and the six declared outcome
measurements taken from that same crate at harvest. 24 crates were fed brewery spent grain and 24
were fed sorted supermarket vegetable waste.

### Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `crate_id` | text | none | Crate label, `CR01` through `CR48`. One per crate, unique across the file. |
| `substrate` | text | none | Feed substrate for that crate. Exactly two distinct values: `spent_grain` (brewery spent grain) and `vegetable_waste` (sorted supermarket vegetable waste). |
| `mean_larval_fresh_mass_mg` | number, 1 decimal | milligrams | Declared outcome 1. Mean fresh mass of an individual larva at harvest in that crate. |
| `fresh_larval_yield_g` | integer | grams | Declared outcome 2. Total harvested fresh larval mass taken from that crate. |
| `crude_protein_pct_dm` | number, 1 decimal | percent of dry matter | Declared outcome 3. Crude protein content of the larvae harvested from that crate. |
| `crude_fat_pct_dm` | number, 1 decimal | percent of dry matter | Declared outcome 4. Crude fat content of the larvae harvested from that crate. |
| `substrate_reduction_pct` | number, 1 decimal | percent | Declared outcome 5. Share of the crate's starting substrate mass that was consumed by harvest. |
| `development_time_days` | number, 1 decimal | days | Declared outcome 6. Days from seeding to the appearance of the first prepupae in that crate. |

The six outcome columns appear in the fixed order the trial plan declared them.

### Observed ranges in the file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `mean_larval_fresh_mass_mg` | 122.9 | 221.6 |
| `fresh_larval_yield_g` | 663 | 1109 |
| `crude_protein_pct_dm` | 32.5 | 45.6 |
| `crude_fat_pct_dm` | 20.3 | 37.0 |
| `substrate_reduction_pct` | 29.0 | 60.6 |
| `development_time_days` | 12.0 | 18.0 |

## How the values were produced

`make_data.py` draws each crate's six outcomes from normal distributions whose centres and spreads
match the typical production levels for the two substrates. Each crate also gets a single
crate-level performance factor, so within one crate the outcomes move together the way real crates
do: a crate that runs warm and well aerated tends to show heavier larvae, a larger yield, more
substrate reduction, and a shorter time to first prepupae. Values are clipped to physically
sensible limits and rounded to the precision the production log uses.
