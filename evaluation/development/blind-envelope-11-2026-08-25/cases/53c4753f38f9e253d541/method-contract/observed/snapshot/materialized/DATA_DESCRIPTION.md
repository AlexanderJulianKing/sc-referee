# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator. Running it with Python writes `harvest_records.csv`. The seed is fixed at the top of the file, so a re-run reproduces the same file. |
| `harvest_records.csv` | The harvest record for the quinoa deficit-irrigation experiment. This is the analysis input. |

## `harvest_records.csv`

**What one row represents:** one individually potted quinoa plant. Sixty-four plants of a
single accession were grown outdoors in a common garden, on the same substrate, sown on the
same day. Each plant was harvested and measured on its own, so a row holds that one plant's
pot tag, its five measured outcomes, and the irrigation regime its pot was assigned.

The file has a header row and 64 data rows: 32 plants under full irrigation and 32 under
deficit irrigation. There are no missing cells. The five outcome columns appear in the order
the outcomes were declared in the experimental plan.

### Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | none | Pot tag for the plant, `QNA-001` through `QNA-064`. Unique for every row. |
| `seed_yield_g` | number | grams | Total cleaned seed harvested from that plant, rounded to 0.1 g. |
| `thousand_seed_weight_g` | number | grams | Weight of one thousand seeds from that plant's harvest, rounded to 0.01 g. A measure of how heavy each individual seed is. |
| `plant_height_cm` | number | centimetres | Height of the plant from the substrate surface to the top of the panicle at harvest, rounded to 0.1 cm. |
| `seed_saponin_mg_g` | number | milligrams per gram | Saponin content of that plant's seed, rounded to 0.01 mg/g. Saponin is the bitter coating on quinoa seed. |
| `midday_leaf_water_potential_mpa` | number | megapascals | Midday leaf water potential for that plant, recorded as a positive tension, rounded to 0.01 MPa. Higher numbers mean the leaf was pulling harder on its water, that is, the plant was more water stressed. |
| `irrigation_regime` | text | none | Which watering regime the pot was assigned. Exactly two values: `full` (full irrigation) and `deficit` (about half the water from the start of flowering). 32 rows each. |

### Ranges in the delivered file

These are the values actually present in `harvest_records.csv`, given here so the file's
contents can be checked at a glance.

| Column | Full irrigation (mean, SD) | Deficit irrigation (mean, SD) | Overall range |
| --- | --- | --- | --- |
| `seed_yield_g` | 23.80, 4.41 | 18.16, 4.15 | 10.9 to 31.0 |
| `thousand_seed_weight_g` | 3.01, 0.49 | 2.79, 0.39 | 1.88 to 3.89 |
| `plant_height_cm` | 115.83, 10.43 | 100.58, 11.02 | 78.0 to 132.4 |
| `seed_saponin_mg_g` | 4.53, 1.30 | 5.30, 1.20 | 1.74 to 7.69 |
| `midday_leaf_water_potential_mpa` | 1.18, 0.34 | 1.77, 0.31 | 0.58 to 2.43 |

## How the file was generated

`make_data.py` draws every plant from a fixed random seed. Each plant first gets a single
latent vigour score, which is the plant-level quality a technician would notice before any
measurement: a big, well established plant tends to be taller, to fill more seed, and to carry
slightly heavier individual seeds. All five outcomes are drawn around that shared score, which
is what makes the columns correlate with each other the way real harvest records do instead of
looking like five unrelated columns. On top of that, the irrigation regime shifts the mean of
each outcome. Values are then pulled back to a physically sensible floor (no negative yield, no
zero-tension leaf) and rounded to the precision of the balance or instrument that would have
produced them.
