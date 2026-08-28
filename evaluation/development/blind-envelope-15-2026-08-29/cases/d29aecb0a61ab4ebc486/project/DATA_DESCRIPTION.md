# Data description

`data.csv` holds the measurements from a pasta drying temperature study on durum semolina
spaghetti. Fifty production lots were extruded and dried separately on the same line, twenty-five
on a low temperature cycle peaking at 55 degrees Celsius and twenty-five on a very high temperature
cycle peaking at 90 degrees Celsius. Formulation, extrusion and packaging were identical across
lots. Each lot was sampled once after drying.

## What one row represents

One row is one production lot: the lot's identifier, the drying cycle it was dried on, and the
single post-drying measurement of each of the five declared outcomes for that lot. There are 50
rows plus a header row, one row per lot, with no repeated rows, no summary rows and no blank cells.

## Columns, in file order

| Column | Meaning | Unit | Type |
| --- | --- | --- | --- |
| `lot_id` | Identifier of the production lot, `lot_` followed by a zero-padded lot number from `lot_01` to `lot_50` | none | text |
| `drying_cycle` | Drying cycle the lot was dried on: `LT` for the low temperature cycle peaking at 55 degrees Celsius, `VHT` for the very high temperature cycle peaking at 90 degrees Celsius | none | text, two labels |
| `cooking_loss_pct` | Cooking loss, the solids lost to the cooking water, as a percentage of the dry weight of the sample | percent of dry weight | number, 2 decimals |
| `optimal_cooking_time_min` | Optimal cooking time, the time to disappearance of the uncooked core | minutes | number, 1 decimal |
| `firmness_n` | Firmness of the cooked strand, the maximum cutting force | newtons (N) | number, 2 decimals |
| `colour_b_star` | Colour yellowness of the dried pasta on the b star axis of the CIE L\*a\*b\* colour space | none (colour scale value) | number, 2 decimals |
| `furosine_mg_100g_protein` | Furosine content, a marker of heat damage to lysine during drying | milligrams per 100 g of protein | integer |

The five outcome columns appear in the order in which the study plan declared them: cooking loss,
optimal cooking time, firmness, colour b star, furosine.

## Completeness and ranges

Every lot has a value for every outcome, so there are no missing values anywhere in the file. The
group column contains exactly the two labels `LT` and `VHT`, with 25 lots carrying each label.
Cooking loss runs from 3.83 to 8.39 percent, optimal cooking time from 7.7 to 12.7 minutes,
firmness from 1.18 to 2.64 newtons, colour b star from 22.10 to 32.66, and furosine from 46 to 445
milligrams per 100 g of protein. Values are rounded to the precision each laboratory method
reports.
