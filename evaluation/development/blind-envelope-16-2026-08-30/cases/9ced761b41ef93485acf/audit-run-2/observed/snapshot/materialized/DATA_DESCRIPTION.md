# Data description

## File

`chickpea_inoculation.csv`

Screenhouse experiment on rhizobial seed inoculation of chickpea. Sixty individually potted
chickpea plants were harvested at pod fill. Thirty plants were grown from seed treated with a
commercial rhizobial slurry, and thirty were grown from untreated seed. Every plant was measured
for every outcome.

## What one row represents

One row is one harvested chickpea plant, that is, one pot. The row carries that plant's
identifier, its seed treatment, and its measured value for each of the seven outcomes. There are
60 rows plus a header row. No value is missing.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `plant_id` | text | none | Per-plant identifier, `P01` through `P60`. One value per pot, no repeats. |
| `inoculation` | text | none | Seed treatment group. Exactly two values: `inoculated` (30 plants, rhizobial slurry seed treatment) and `uninoculated` (30 plants, untreated seed). |
| `shoot_dw_g` | number | grams per plant | Shoot dry weight. |
| `root_dw_g` | number | grams per plant | Root dry weight. |
| `nodule_no` | integer | count per plant | Number of root nodules. |
| `nodule_dw_mg` | number | milligrams per plant | Dry weight of all nodules on the plant. |
| `shoot_n_pct` | number | percent of dry matter | Nitrogen concentration in the shoot. |
| `pod_no` | integer | count per plant | Number of pods. |
| `seed_yield_g` | number | grams per plant | Seed yield. |

The seven outcome columns appear in the order the experiment declared them in advance: shoot dry
weight, root dry weight, nodule number, nodule dry weight, shoot nitrogen concentration, pod
number, then seed yield.

## Notes on the values

- Column names are lower case with words joined by underscores. Each outcome column ends with a
  short abbreviation of its unit.
- Rows are stored in pot order, and the two seed treatments are mixed through that order because
  the pots were randomised across the bench. Rows are not grouped by treatment.
- `nodule_dw_mg` is the total nodule mass for the plant, so it moves with `nodule_no`. A plant with
  zero nodules has zero nodule dry weight.
- Values are recorded to the precision of the bench measurement: two decimals for the dry weights
  in grams and for shoot nitrogen percent, one decimal for nodule dry weight in milligrams, and
  whole numbers for the two counts.
