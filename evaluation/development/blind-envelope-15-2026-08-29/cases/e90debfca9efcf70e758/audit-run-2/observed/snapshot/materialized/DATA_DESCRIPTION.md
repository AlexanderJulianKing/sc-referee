# data.csv

Screenhouse irrigation trial on quinoa. Forty-eight individually potted plants of a
single cultivar, one plant per pot, all sown on the same day in the same growing
medium, randomly allocated to two irrigation waters (24 pots each) and grown to
maturity before individual harvest and measurement.

**One row = one harvested plant (one pot).** The file has 48 data rows plus a header
row. There are no repeated rows, no summary rows, and no blank cells; every plant has
a value for every outcome.

## Columns, in file order

| Column | Meaning | Unit / values |
| --- | --- | --- |
| `plant_id` | Identifier of the individual plant and its pot. Prefix `qn` (quinoa) followed by a zero-padded two-digit number, `qn01` through `qn48`. Unique across the file. | text label, no unit |
| `irrigation_water` | Irrigation water the pot was randomly allocated to. `fresh` = fresh water at about 0.8 dS/m; `brackish` = brackish water at about 12 dS/m. Exactly two labels, 24 plants each. | text label: `fresh` or `brackish` |
| `grain_yield_g` | Grain yield of that plant at harvest. Declared outcome 1. Recorded to 0.1 g. | grams (g) |
| `thousand_seed_weight_g` | Thousand-seed weight for that plant's grain. Declared outcome 2. Recorded to 0.01 g. | grams (g) |
| `plant_height_cm` | Height of that plant at maturity. Declared outcome 3. Recorded to 0.1 cm. | centimetres (cm) |
| `leaf_sodium_mg_g` | Sodium concentration in that plant's leaf tissue. Declared outcome 4. Recorded to 0.01. | milligrams of sodium per gram of leaf dry matter (mg/g) |

The four outcome columns appear in the order the trial protocol declared them, which is
the order shown above.

## Notes

- The identifier column carries no information about which water a pot received; the
  labels in `irrigation_water` are what record the allocation.
- Values are individual plant measurements, not averages of anything.
- The file is fixed input data. Nothing in the project regenerates, simulates, or
  overwrites it.
