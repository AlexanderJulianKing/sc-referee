# Data description: ferret housing-enrichment welfare study

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded Python generator. Running it writes `ferret_welfare.csv`. Re-running it always produces the same file. |
| `ferret_welfare.csv` | The study data set, and the only analysis input. 40 data rows plus one header row. |
| `DATA_DESCRIPTION.md` | This file. |

## `ferret_welfare.csv`

One row per ferret. A row holds one adult ferret's identifier, its four
eight-week welfare summary values, and the housing condition it lived under for
those eight weeks. Each of the 40 ferrets appears exactly once. Every cell is
filled; there are no missing values and no blank cells.

The colony holds 40 adult ferrets, 20 housed in enriched pens (tunnels, digging
substrate, raised platforms, rotating novel objects) and 20 in standard pens
(bedding and a nest box only). The four outcome columns appear in the order the
welfare assessment plan declared them.

### Columns

| # | Column | Type | Unit | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `animal_id` | text | none | Colony identifier for the ferret, `FRT-01` through `FRT-40`. Unique across the 40 rows. |
| 2 | `daily_active_time_min` | number, 1 decimal | minutes per day | Declared outcome 1. Mean daily active time from the animal's accelerometer collar, averaged over the eight weeks. Observed range in this file: 81.1 to 277.9. |
| 3 | `faecal_corticosterone_ng_per_g` | number, 1 decimal | nanograms per gram of faeces | Declared outcome 2. The animal's faecal corticosterone metabolite concentration for the eight-week period. Observed range: 48.6 to 155.9. |
| 4 | `body_mass_change_g` | whole number | grams | Declared outcome 3. Change in body mass across the eight weeks, end mass minus start mass. Negative values mean the animal lost mass. Observed range: -10 to 122. |
| 5 | `stereotypic_bouts_per_hour` | number, 2 decimals | bouts per hour | Declared outcome 4. Stereotypic behaviour bouts recorded per hour of observation, averaged over the eight weeks. Never negative. Observed range: 0.00 to 2.78. |
| 6 | `housing_condition` | text | none | The grouping factor, with exactly two distinct values: `enriched` (20 ferrets) and `standard` (20 ferrets). |

### Row counts

| `housing_condition` | Ferrets |
| --- | --- |
| `enriched` | 20 |
| `standard` | 20 |
| total | 40 |

## How the numbers were produced

`make_data.py` draws every value with a seeded NumPy random generator, so the
CSV is reproducible byte for byte. Each animal first gets a single latent
"welfare tone" value that nudges all four of its outcomes together, so an animal
that moves more also tends to show lower corticosterone and fewer stereotypic
bouts. Each outcome is then drawn around its group's typical level with the
spread from the study plan, floored where a negative value would be impossible,
and rounded the way the colony records that quantity.

The generator scans candidate seeds in a fixed order and keeps the first colony
whose realised group separations match the intended pattern: three outcomes
where the two housing conditions clearly separate and one, body mass change,
where they overlap heavily. That check uses only realised standardised
differences computed with ordinary array arithmetic. No statistical test, no
p-value, and no significance machinery is involved in generating the data.

Values are invented for this exercise. They are not records from a real colony.
