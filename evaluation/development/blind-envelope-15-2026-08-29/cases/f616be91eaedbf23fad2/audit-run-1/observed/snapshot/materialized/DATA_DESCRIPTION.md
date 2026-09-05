# data.csv

Pilot-plant study of firm tofu made with two coagulants. Sixty tofu blocks were produced, each
from its own 500 g batch of the same soybean lot on the same equipment. Thirty blocks were
coagulated with calcium sulfate and thirty with glucono-delta-lactone; every other process
setting was held constant. Each block was measured the day after pressing.

**One row is one tofu block**, identified by `block_id`, with its coagulant group and its six
declared outcome measurements. There are 60 rows plus a single header row. There are no repeated
rows, no summary rows, and no blank cells: every block has a value for every outcome.

## Columns

Columns appear in this order. The six outcome columns are in the order the outcomes were declared
in the study plan.

| Column | Meaning | Unit | Type |
| --- | --- | --- | --- |
| `block_id` | Identifier for the tofu block, `blk_01` through `blk_60`, in production run order | none | text |
| `coagulant` | Coagulant used for that block: `caso4` (calcium sulfate) or `gdl` (glucono-delta-lactone) | none | text, 2 levels |
| `yield_g_per_100g` | Tofu yield: pressed tofu recovered per 100 g of dry soybeans | g per 100 g dry soybeans | number, 1 decimal |
| `hardness_n` | Hardness at 30 percent compression | newtons (N) | number, 2 decimals |
| `syneresis_pct` | Liquid released after 24 hours of refrigerated storage, as a percentage of block weight | percent of block weight | number, 2 decimals |
| `whiteness_index` | Whiteness index of the block surface, on a 0 to 100 scale | unitless (0-100 index) | number, 1 decimal |
| `protein_g_per_100g` | Protein content of the fresh tofu | g per 100 g fresh tofu | number, 2 decimals |
| `ph` | pH of the pressed block | unitless (pH scale) | number, 2 decimals |

## Group sizes

| `coagulant` | Blocks |
| --- | --- |
| `caso4` | 30 |
| `gdl` | 30 |

## Notes on format

- Plain comma-separated text, UTF-8, one header row, no quoting needed.
- Decimal places match the precision the pilot-plant laboratory records for each instrument, so
  every value in a column is written with the same number of decimals.
- `data.csv` is a fixed data file and is not regenerated or overwritten by anything that reads it.
