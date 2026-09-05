# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded Python generator that writes `pouch_shelf_life.csv`. Re-running it reproduces the same file byte for byte. |
| `pouch_shelf_life.csv` | The study data. One row per pouch, 36 data rows plus a header row. |

## What one row represents

One row is one sealed retail pouch of avocado pulp: a single pouch filled from
the one homogenised batch, stabilised by one of the two processing methods,
held at 4 degrees Celsius, and opened once after 21 days of chilled storage.
The three measured columns are the values recorded from that pouch at that
single opening. Each pouch appears exactly once, and every pouch has a value in
every column, so there are no missing cells.

## Columns of `pouch_shelf_life.csv`

| Column | Type | Description |
| --- | --- | --- |
| `pouch_id` | text | Identifier of the pouch, `P01` through `P36`. Unique across the file. Numbering follows the fill order of the batch. |
| `colour_a_star` | number, 2 decimals | Greenness of the pulp, the a* coordinate of instrumental colour. Unitless. Negative values mean green, so a more negative number is a greener pulp. Observed range in this file: -10.03 to -3.21. |
| `residual_ppo_activity_percent` | number, 1 decimal | Residual polyphenol oxidase activity, expressed as a percent of the activity measured in the unprocessed raw pulp. The assay reports no less than 0.5 percent. Observed range: 2.9 to 31.5. |
| `aerobic_plate_count_log10_cfu_per_g` | number, 2 decimals | Total aerobic plate count, in log base ten colony forming units per gram of pulp. The plating method quantifies down to 1.00, which is 10 colony forming units per gram. Observed range: 1.06 to 2.83. |
| `processing_method` | text | The stabilisation method applied to the pouch. Exactly two distinct values: `high_pressure` (high-pressure processing) and `thermal_pasteurised` (conventional mild thermal pasteurisation). 18 pouches carry each value. |

The three measured columns appear in the order the shelf-life protocol declares
them: colour first, then residual enzyme activity, then plate count.

## How the file was produced

`make_data.py` draws each measurement from a normal distribution centred on the
level the protocol expects for that method at 21 days, with the pouch-to-pouch
spread seen on this product line, then rounds to the precision the bench
instruments report. Draws that would fall below the reporting floor of the
polyphenol oxidase assay or below the plate-count quantification limit are
redrawn rather than kept, so no value in the file sits below what the
laboratory could actually report. The two methods were assigned to the fill
order at random, which is why they are interleaved in the file rather than
grouped. The random seed is fixed at 88.
