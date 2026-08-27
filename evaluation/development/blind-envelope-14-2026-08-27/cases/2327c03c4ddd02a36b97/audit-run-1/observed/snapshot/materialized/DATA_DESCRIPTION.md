# Data description

## File

`storage_trial.csv` — one header row and 60 data rows, comma separated, no missing cells.

## What one row represents

One row is one individually tracked storage crate. Each crate holds 25 kg of ware potatoes of a
single cultivar drawn from the same harvest lot. Each crate was randomly assigned to one of the two
sprout suppressant treatments, held for six months at 8 degrees Celsius and 95 percent relative
humidity, and then assessed. The six outcome columns are that crate's assessment values, so the
crate is the unit of measurement and every crate has a value for every declared outcome.

Thirty crates were assigned to `orange_oil` and thirty to `spearmint_oil`.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `crate_id` | text | none | Crate label, `C01` through `C60`, unique per row. |
| `suppressant` | text | none | Treatment group. Exactly two values: `orange_oil` and `spearmint_oil`. |
| `sprout_length_mm` | number | millimetres | Declared outcome 1. Mean sprout length across the tubers in the crate, one decimal place. `0.0` means the crate broke no dormancy. |
| `weight_loss_pct` | number | percent | Declared outcome 2. Cumulative weight loss of the crate over the six month storage period, two decimal places. |
| `firmness_n` | number | newtons | Declared outcome 3. Tuber firmness by penetrometer, crate mean, one decimal place. |
| `reducing_sugars_mg_per_g` | number | mg per g fresh weight | Declared outcome 4. Reducing sugars in the crate sample, two decimal places. |
| `sprouted_tubers_pct` | number | percent of the crate | Declared outcome 5. Share of tubers in the crate showing any sprouting, one decimal place. |
| `soft_rot_pct` | number | percent of the crate | Declared outcome 6. Share of tubers in the crate with soft rot, one decimal place. `0.0` means no rot was found in that crate. |

The six outcome columns appear in the declared family order, columns 3 through 8 of the file.

## Value ranges and recording conventions

Values are recorded at the precision the station's instruments report: sprout length and firmness to
0.1, weight loss and reducing sugars to 0.01, and the two percentage outcomes to 0.1. All
percentages stay inside their possible range, and both percentage-of-crate columns stay between 0
and 100. Observed spans in this file are:

| Column | Minimum | Maximum |
| --- | --- | --- |
| `sprout_length_mm` | 0.0 | 24.3 |
| `weight_loss_pct` | 2.32 | 8.57 |
| `firmness_n` | 13.7 | 26.4 |
| `reducing_sugars_mg_per_g` | 0.64 | 3.13 |
| `sprouted_tubers_pct` | 0.0 | 44.8 |
| `soft_rot_pct` | 0.0 | 8.0 |

Outcomes measured on the same crate are related the way they are in a real store: a crate with
longer sprouts also shows a larger share of sprouted tubers, and a crate that lost more water is
softer and a little more prone to rot.
