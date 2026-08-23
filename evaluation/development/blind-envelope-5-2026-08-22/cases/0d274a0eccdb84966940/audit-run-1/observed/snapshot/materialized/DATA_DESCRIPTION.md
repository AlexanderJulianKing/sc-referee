# Data description

## File

`data.csv` — the single data file for this project. Comma-separated, one header line plus 144 data
rows. It is produced by `make_data.py` (Python standard library only, fixed random seed 20260822),
so re-running that script reproduces the file exactly.

## What one row represents

One row is **one novel-object recognition test run by one rat on one day**. It is not one animal.
Each rat was tested eight times, on separate days with a different object pair each time, so each
rat appears on **eight rows** of the file. The rows for a rat are not independent of one another:
they share the same animal.

- Experimental units (animals): **18 rats**
- Rows (test runs): **144** = 18 rats x 8 runs
- The file is left at run level. Any reduction to one value per animal happens in the analysis, not
  in this file.

## Groups

Housing has two levels, assigned to whole animals, nine rats each:

| housing | rats | rows |
| --- | --- | --- |
| `enriched` | 9 | 72 |
| `standard` | 9 | 72 |

- `enriched`: cages with tunnels, ropes and rotating objects.
- `standard`: standard laboratory cages.

Because housing was assigned per animal, every one of a rat's eight rows carries the same housing
label.

## Columns

Columns appear in this order.

| # | Column | Type | Units / values | Meaning |
| --- | --- | --- | --- | --- |
| 1 | `rat_id` | text | animal code, `BN-101` to `BN-118` | Identifies the animal. Repeats across the eight rows belonging to that rat. 18 distinct values. |
| 2 | `housing` | text | `enriched` or `standard` | Housing condition of the animal. Constant within a `rat_id`. |
| 3 | `run_number` | integer | 1 to 8 | Which of that rat's eight test sessions this row is. Unique within a `rat_id`; `rat_id` + `run_number` together identify a row. |
| 4 | `exploration_time_s` | number, 1 decimal | seconds, 15.0 to 45.0 | Total time the rat spent exploring both objects during that run. |
| 5 | `discrimination_index` | number, 3 decimals | proportion, 0 to 1 | Outcome. Share of that run's total exploration time spent on the novel object. 0.5 means no preference; higher means more time on the novel object. |

## How the values were generated

Simulated, not collected from animals. Each rat was given a stable animal-level tendency (a value
drawn once per rat) and then each of its eight runs added independent run-to-run noise on top, so
runs within a rat are more alike than runs across rats. Group centres were set to the ranges the
study description calls realistic: roughly 0.48 to 0.66 per run for standard-housed rats and roughly
0.58 to 0.78 for enriched rats. Exploration time was drawn independently of the index and clipped to
15 to 45 seconds.

## Completeness

No missing values. Every rat has all eight runs. No duplicate `rat_id` + `run_number` pairs.
