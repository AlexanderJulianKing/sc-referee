# Data description

## Files

### `make_data.py`

Deterministic seeded generator (`SEED = 20260826`, Python `random.Random`). Running it with the
project's Python writes `scorpions.csv`. Re-running it reproduces the same file exactly.

### `scorpions.csv`

The analysis input. 30 data rows plus one header row. Comma-separated, UTF-8, Unix line endings.

**What one row represents:** one adult giant hairy scorpion, hand-collected at night under
ultraviolet light and measured once in a field laboratory within twelve hours of capture, then
released at its capture point. The animal is the unit of the study. Each scorpion appears exactly
once. There are no blank cells.

**Columns, in file order:**

| Column | Holds | Unit / values |
| --- | --- | --- |
| `scorpion_id` | Identifier for the individual animal, `SC001` through `SC030` | text, unique per row |
| `group` | Capture site type | text, exactly two values: `burned` (inside the two-year-old burn scar) and `unburned` (adjacent unburned creosote scrub, matched on soil type and elevation) |
| `body_mass_g` | Body mass of the animal at measurement | grams, 2 decimal places |
| `haemolymph_protein_g_l` | Haemolymph total protein concentration from a single haemolymph draw | grams per litre, 1 decimal place |
| `metabolic_rate_ml_o2_h` | Resting metabolic rate by closed-chamber respirometry at 25 degrees Celsius | millilitres of oxygen per hour, 3 decimal places |

The three outcome columns appear in the order the field protocol declared them: body mass, then
haemolymph protein, then resting metabolic rate.

**Row counts:** 15 rows with `group = burned` (`SC001`–`SC015`) and 15 rows with
`group = unburned` (`SC016`–`SC030`).

**Value ranges in the generated file:**

| Column | Minimum | Maximum |
| --- | --- | --- |
| `body_mass_g` | 4.57 | 10.29 |
| `haemolymph_protein_g_l` | 31.6 | 67.4 |
| `metabolic_rate_ml_o2_h` | 0.073 | 0.252 |

These sit inside the typical adult ranges stated in the field protocol: about 3.5 to 11 grams,
about 28 to 72 grams per litre, and about 0.04 to 0.32 millilitres of oxygen per hour. The
generator draws each value from a normal distribution with a per-group mean and standard deviation,
redrawing anything that falls outside those hard plausibility limits, so animal-to-animal variation
within each site type is realistic and the two site types overlap.
