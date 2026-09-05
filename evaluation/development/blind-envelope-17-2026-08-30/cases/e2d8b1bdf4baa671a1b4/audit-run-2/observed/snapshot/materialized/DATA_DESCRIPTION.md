# Data description

File: `daphnia_temperature.csv`

Rearing-temperature experiment on the water flea *Daphnia magna*. Eighty animals from a single
clonal line were reared individually from birth, forty in vessels held at 18 degrees Celsius and
forty at 24 degrees Celsius, on the same algal feeding regime and the same water renewal schedule.
Rearing temperature is the only condition that differs between the two sets of vessels.

## What one row represents

One row is one animal: a single individually reared *Daphnia magna*, followed from birth, with its
rearing temperature and its four declared life-history outcomes. The file has a header row plus 80
data rows, one per animal, 40 animals per temperature. Every animal has a value in every column;
there are no missing cells, no repeated animals and no extra rows.

## Columns

The file has six columns, in this order.

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `animal_id` | text | none | Identifier for the animal: the prefix `dm` plus a zero-padded two-digit serial number, `dm01` through `dm80`. Unique across the file. |
| `temperature_c` | integer | degrees Celsius | Group column. Rearing temperature of the vessel the animal was held in. Exactly two distinct values: `18` and `24`. |
| `age_first_brood_days` | number | days | Declared outcome 1. Age at first brood release, counted from birth. Vessels were inspected twice a day, so values fall on a 0.5-day grid and are written with one decimal place. |
| `body_length_day14_mm` | number | millimetres | Declared outcome 2. Body length on day fourteen, measured with an ocular micrometer on a stereomicroscope and recorded to 0.01 mm. |
| `offspring_day21` | integer | count of neonates | Declared outcome 3. Cumulative number of offspring released by day twenty-one. A whole count, so no decimal places. |
| `heart_rate_day10_bpm` | integer | beats per minute | Declared outcome 4. Heart rate on day ten, from beats counted over a timed window under the stereomicroscope and scaled to a whole number of beats per minute. |

Columns 3 through 6 are the four outcomes of the declared outcome family, listed here in the order
fixed in the experimental plan.

## Format notes

- Plain comma-separated text, UTF-8, Unix line endings, one header row.
- No quoting is needed: no field contains a comma.
- Numeric columns carry no thousands separators and no unit suffixes; units live in the column names
  and in the table above.
- Values are fixed and committed in the file. Nothing in the data is produced at analysis time.
