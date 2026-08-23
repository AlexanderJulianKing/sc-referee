# Data description

## File

`compost_cores.csv` is the only data file. It holds the raw core-sampling data
from the composting bulking-agent trial: 1 header row plus 80 data rows.

The file was produced by `make_data.py` (Python standard library only, fixed
random seed 20260822). Re-running that script rewrites the same file byte for
byte. The values are invented for this project, not measurements from a real
facility.

## What one row represents

One row is one core sample: a single core taken from one point along one
windrow and analysed on its own.

## Units and counts

- 16 windrows, each managed for twelve weeks.
- 8 windrows built with shredded wood chip, 8 built with chopped straw.
- 5 cores taken from evenly spaced points along each windrow.
- 16 x 5 = 80 core rows in the raw file.

The five cores from a windrow are spatial subsamples of the same pile, so they
are not independent piles. The windrow is the experimental unit; the core rows
are the sampling detail sitting behind each windrow.

## The two groups

| bulking_agent | Meaning | Windrows | windrow_id values | Core rows |
| --- | --- | --- | --- | --- |
| `woodchip` | Green waste bulked with shredded wood chip | 8 | W01-W08 | 40 |
| `straw` | Green waste bulked with chopped straw | 8 | W09-W16 | 40 |

The design is balanced: every windrow contributes exactly 5 cores, and every
group contains exactly 8 windrows.

## Columns

Columns appear in the file in this order.

| # | Column | Type | Description |
| --- | --- | --- | --- |
| 1 | `windrow_id` | text | Identifier of the windrow the core came from. Values `W01` through `W16`, one per windrow, repeated on the 5 rows belonging to that windrow. |
| 2 | `bulking_agent` | text | Which bulking agent that windrow was built with. Exactly two values: `woodchip` and `straw`. Constant within a windrow. |
| 3 | `core_number` | integer | Position label of the core within its windrow, `1` through `5`, following the evenly spaced sampling points along the pile. Unique within a windrow; it is a label, not a measurement. |
| 4 | `c_to_n_ratio` | decimal | Carbon to nitrogen ratio of the finished compost in that core, recorded to one decimal place. This is the outcome. |

`windrow_id` together with `core_number` identifies a row uniquely.

## How the values were built

Each core value is the sum of three parts:

- a group mean of 18.5 for `woodchip` and 15.2 for `straw`;
- a windrow offset drawn with a standard deviation of 1.2, so whole piles sit a
  little above or below their group average depending on how they were turned;
- core-to-core noise drawn with a standard deviation of 1.6, because the
  material in a pile is not perfectly mixed.

The sum is rounded to one decimal place and held inside the range 11.0 to 24.0.
In the generated file the observed values run from 11.0 to 23.2, and one value
sits on the lower bound.

## Missing data

There are none. Every row has all four fields filled in, and no windrow is
missing a core.
