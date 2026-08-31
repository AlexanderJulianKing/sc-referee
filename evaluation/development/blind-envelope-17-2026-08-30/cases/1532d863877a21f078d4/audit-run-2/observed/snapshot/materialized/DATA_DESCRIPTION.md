# Data description

File: `sunflower_trial.csv`

Field agronomy trial at the research station testing whether coating sunflower seed with a
microbial biostimulant before sowing improves crop performance. Seventy-two individually tagged
sunflower plants were grown in a single uniform field under one management regime: thirty-six from
biostimulant-coated seed and thirty-six from untreated seed of the same cultivar and seed lot. Each
plant was measured individually at flowering and at harvest.

**One row is one tagged sunflower plant**, carrying its seed treatment and its value for each of the
five declared outcome variables. The file has 72 data rows plus a header row, 36 plants per seed
treatment, and no missing cells.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `plant_id` | text | — | Plant tag: prefix `SF-` plus a zero-padded serial number, `SF-001` to `SF-072`. Unique per plant. |
| `seed_treatment` | text | — | Seed treatment group. Exactly two values: `untreated` (uncoated seed) and `coated` (biostimulant-coated seed). |
| `plant_height_cm` | integer | centimetres | Outcome 1. Plant height measured at flowering, recorded to the nearest centimetre. |
| `head_diameter_cm` | number | centimetres | Outcome 2. Capitulum (seed head) diameter at harvest, recorded to 0.1 cm. |
| `filled_seed_number` | integer | count | Outcome 3. Number of filled seeds in the head, counted at harvest. |
| `thousand_seed_mass_g` | number | grams | Outcome 4. Mass of one thousand seeds from that plant, recorded to 0.1 g. |
| `seed_oil_content_pct` | number | percent | Outcome 5. Seed oil content as a percentage of seed dry mass, recorded to 0.1 percent. |

The five outcome columns appear in the declared outcome order fixed before the season began:
plant height, head diameter, filled seed number, thousand-seed mass, seed oil content.

## Provenance

Values are fixed and committed in the CSV; nothing in the data file is produced at analysis run
time. The measurements were laid down by `make_data.py`, which stays alongside the data as a record
of how the file was written.
