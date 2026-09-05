# Data description

File: `mussel_rearing_data.csv`

One row is one individually tagged juvenile freshwater pearl mussel from the captive cohort,
measured at the end of the twelve-month rearing trial. The file holds 66 rows plus a header row:
33 juveniles reared on a fine sand bed and 33 reared on a coarse gravel bed, all in flow-through
cells supplied from the same header tank. Every mussel has a value for every outcome; there are no
missing cells and no extra rows.

## Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `mussel_tag` | text | none | Individual tag identifier, prefix `PM` plus a zero-padded three-digit serial (`PM001` to `PM066`). Unique for every row. |
| `substrate` | text | none | Rearing substrate group. Exactly two distinct values: `sand` (fine sand bed) and `gravel` (coarse gravel bed). |
| `shell_length_increment_mm` | number | millimetres | Growth in shell length over the twelve months, recorded to 0.01 mm with digital calipers. |
| `wet_mass_gain_g` | number | grams | Gain in wet mass over the twelve months, recorded to 0.001 g. |
| `condition_index_pct` | number | percent | Condition index: soft tissue dry mass as a percentage of shell dry mass, to 0.01. |
| `foot_glycogen_mg_per_g` | number | milligrams per gram dry mass | Glycogen concentration in foot tissue, to 0.1 mg/g. |
| `clearance_rate_l_per_h` | number | litres per hour per individual | Clearance rate from the standard feeding assay, to 0.001 L/h. |

The five outcome columns appear in the order declared in the rearing protocol: shell length
increment, wet mass gain, condition index, foot glycogen, clearance rate.

## Notes

- Values are fixed and committed in the CSV. They are not produced at analysis time.
- Rows are ordered by tag serial. Substrate assignment is mixed across the serial order, not
  blocked, so group membership must be read from the `substrate` column.
- Individual scatter within each group is wide, as expected for a captive cohort with variable
  individual growth, and the two groups overlap on every outcome.
