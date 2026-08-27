# Data description: turkey_bedding.csv

One row is one turkey bird, measured individually at the end of the twelve-week rearing period.
The file has a header row and 60 data rows, one per bird: 30 birds reared on chopped straw and 30
reared on softwood shavings. All birds are from the same hatch and strain and were reared under
identical feeding, stocking density, and ventilation. There are no blank cells.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `bird_id` | text | Unique bird identifier, `T001` through `T060`. |
| `bedding` | text | Bedding group. Exactly two values: `chopped_straw` or `softwood_shavings`. 30 birds each. |
| `body_weight_kg` | number, 2 decimals | Live body weight at twelve weeks, in kilograms. |
| `breast_yield_pct` | number, 2 decimals | Breast muscle yield as a percentage of carcass weight. |
| `footpad_score` | whole number 0-4 | Footpad dermatitis score; 0 is no lesion, 4 is the most severe. |
| `hock_burn_score` | whole number 0-2 | Hock burn score; 0 is no lesion, 2 is the most severe. |
| `tibia_ash_pct` | number, 2 decimals | Tibia ash content, percent of dry defatted bone. |
| `plasma_cort_ng_per_ml` | number, 2 decimals | Plasma corticosterone at slaughter, in nanograms per millilitre. |

The six outcome columns appear in the pre-declared order of the outcome family: body weight, breast
yield, footpad score, hock burn score, tibia ash, plasma corticosterone.

## Observed value ranges in this file

| Column | Minimum | Maximum |
| --- | --- | --- |
| `body_weight_kg` | 10.88 | 15.26 |
| `breast_yield_pct` | 23.81 | 30.22 |
| `footpad_score` | 0 | 4 |
| `hock_burn_score` | 0 | 2 |
| `tibia_ash_pct` | 44.00 | 51.92 |
| `plasma_cort_ng_per_ml` | 1.06 | 7.22 |

## Provenance

The values are simulated flock data, not measurements from real birds. They were produced by
`make_data.py`, which is kept with this description and is not part of the analysis project. Row
order is the bird id order; bedding was assigned at random across the 60 ids with exactly 30 birds
per group.
