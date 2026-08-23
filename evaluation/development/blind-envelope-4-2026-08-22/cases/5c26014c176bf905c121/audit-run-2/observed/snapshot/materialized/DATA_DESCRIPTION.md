# Data description

## File

`oyster_shell_height.csv` is the only data file for this project. It holds one header row and
168 data rows.

## What one row is

One row is one measured Pacific oyster. Each oyster was removed from a grow-out basket after the
twenty-week trial and measured once for shell height.

## Units in the study

The trial ran on 14 mesh grow-out baskets hung along a single longline. Twelve oysters were removed
and measured from each basket, so there are 14 baskets, 168 measured oysters, and 168 data rows.
Every basket contributes exactly 12 rows. The 12 rows that share a `basket_id` are 12 separate
animals that were subsampled from that one basket.

## The two groups

`density_group` splits the 14 baskets into two stocking treatments, 7 baskets each:

| Group      | Meaning                          | Baskets | Basket IDs                    | Oysters |
|------------|----------------------------------|---------|-------------------------------|---------|
| `standard` | the farm's standard stocking density | 7   | B01, B03, B05, B07, B09, B11, B13 | 84  |
| `reduced`  | reduced stocking density          | 7       | B02, B04, B06, B08, B10, B12, B14 | 84  |

The two treatments alternate along the longline, so treatment is not tied to position on the line.

## Columns

The columns appear in this order.

| # | Column            | Type            | Values                                    | Meaning |
|---|-------------------|-----------------|-------------------------------------------|---------|
| 1 | `basket_id`       | text label      | `B01` through `B14` (14 distinct values)   | Identifies the grow-out basket the oyster came from. |
| 2 | `density_group`   | text label      | `standard` or `reduced`                    | The stocking density treatment applied to that basket. Constant within a basket. |
| 3 | `oyster_number`   | integer         | 1 through 12                               | Counter for the oysters taken from one basket. It restarts at 1 in every basket, so it identifies an oyster only when paired with `basket_id`. |
| 4 | `shell_height_mm` | decimal number  | 45.1 to 82.5 in this file                  | Shell height of that oyster in millimetres, recorded to one decimal place. |

There are no missing values in any column.

## How the values were produced

The data are invented, not measured, and are not taken from any published dataset. The generator is
`make_data.py`, which uses only the Python standard library and a fixed random seed
(`SEED = 20260830`), so rerunning it reproduces the file byte for byte.

Each shell height is the sum of three parts:

1. a group mean, set at 61.5 mm for `standard` and 68.0 mm for `reduced`;
2. a basket offset drawn with a standard deviation of 2.8 mm and capped at 4.5 mm either way, which
   shifts all 12 oysters in a basket up or down together to stand for where the basket hung on the
   line (the seven offsets inside a group are re-centred on zero so the group means land on target);
3. an oyster-level deviation drawn with a standard deviation of 6.0 mm.

Values are rounded to one decimal place and redrawn if they fall outside 45.0 to 85.0 mm, which
keeps every recorded height inside a believable range for the species and the grow-out period.

## Summary numbers in the file as generated

| Group      | Oysters | Mean shell height (mm) | SD (mm) | Min (mm) | Max (mm) |
|------------|---------|------------------------|---------|----------|----------|
| `standard` | 84      | 61.61                  | 6.76    | 45.1     | 76.7     |
| `reduced`  | 84      | 67.92                  | 6.24    | 53.9     | 82.5     |

Basket mean shell heights range from 55.58 mm (B07, standard) to 72.81 mm (B12, reduced).
