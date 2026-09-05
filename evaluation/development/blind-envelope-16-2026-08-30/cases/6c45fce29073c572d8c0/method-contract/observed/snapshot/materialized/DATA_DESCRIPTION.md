# Data description: juvenile lobster shelter trial

File: `lobster_shelter_trial.csv`

## What one row represents

One row is one individually reared juvenile European lobster, followed for 60 days from a single
settlement cohort. The row carries that animal's shelter treatment and its value for each of the
five declared outcomes. The file holds 72 rows, one per animal, plus a header row. Every animal was
measured on every outcome, so there are no missing values and no animal appears twice.

## Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `lobster_id` | text | none | Short identifier for the individual animal, `L01` through `L72`. Unique in the file. |
| `shelter_type` | text | none | Rearing shelter the animal was held with. Exactly two values: `crushed_shell` (crushed shell substrate, 36 animals) and `plastic_tube` (moulded plastic tube shelters, 36 animals). |
| `carapace_increment_mm` | number | millimetres | Declared outcome 1. Growth in carapace length over the 60 days. |
| `mass_gain_g` | number | grams | Declared outcome 2. Wet mass gained over the 60 days. |
| `moult_count` | whole number | count | Declared outcome 3. Number of moults the animal completed during the 60 days. |
| `shelter_time_s` | whole number | seconds | Declared outcome 4. Time the animal spent sheltering during one standard ten minute observation, so the value can run from 0 to 600. |
| `haemolymph_protein_g_l` | number | grams per litre | Declared outcome 5. Total protein in the haemolymph, sampled at the end of the trial. |

The five outcome columns appear in the order the experiment declared them in advance: carapace
increment, mass gain, moult count, sheltering time, haemolymph protein.
