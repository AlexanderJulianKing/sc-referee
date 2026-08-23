# Data description

## The file

One data file: `herbage_mass.csv`. It holds 161 lines: one header line and 160 data rows.

## What one row is

**One row is one grid sampling point inside one paddock.** It is not a paddock, and it is not a
farm. At that point the standing herbage was cut, dried and weighed, and the sward height was
measured.

Because ten sampling points were placed on a fixed grid inside every paddock, **each paddock appears
on ten separate rows**. The ten rows that share a `paddock_name` are subsamples of the same fenced
area, not ten independent paddocks.

## How many units, how many rows

| Level | Count |
| --- | --- |
| Paddocks (the units that were assigned to a rotation) | 16 |
| Paddocks per rotation | 8 |
| Grid sampling points per paddock | 10 |
| Rows in the file | 160 |

The rotation was assigned to the whole fenced paddock, so the paddock is the unit that was
randomised. The 160 rows describe the sampling effort inside those 16 units.

## The two groups

The `rotation` column holds exactly two values, eight paddocks each.

- **`fast_rotation`** — short, intense grazing bouts followed by a long rest.
  Paddocks: Birken Shaw, Cauldron Park, High Fell Intake, Kirk Ley, Nether Bught, Slack Burn,
  Stey Brae, Windy Slap.
- **`set_stocking`** — the station's continuous set-stocking, the comparison practice.
  Paddocks: Brackens Head, Corrie Park, Lang Rigg, Muirside Fauld, Peat Hags, Rashy Haugh,
  Sheil Bank, Whinny Knowe.

Each paddock belongs to one rotation only, and keeps that rotation on all ten of its rows.

## Columns

The columns appear in this order.

| # | Column | Type | Meaning |
| --- | --- | --- | --- |
| 1 | `paddock_name` | text | Name of the fenced paddock the point sits in, written the way a hill farm names its fields (for example `Whinny Knowe`). 16 distinct values, each repeated on 10 rows. This is the identifier of the experimental unit. |
| 2 | `rotation` | text | Which grazing treatment the whole paddock was assigned. Exactly two values: `fast_rotation` or `set_stocking`. Constant within a paddock. |
| 3 | `grid_point` | whole number | Which of the ten fixed grid positions inside that paddock the sample came from. Runs 1 to 10 within every paddock. It labels a position, so it carries no order or size meaning across paddocks: point 4 in one paddock has nothing to do with point 4 in another. |
| 4 | `sward_height_cm` | number, 1 decimal place | Height of the sward at that point, in centimetres. Observed range in the file: 3.0 to 16.6. |
| 5 | `herbage_kg_dm_ha` | whole number | **The outcome.** Standing herbage mass at that point, in kilograms of dry matter per hectare, rounded to whole numbers. Observed range in the file: 1021 to 3300. |

## Spread inside the file

Herbage mass varies both between paddocks and between points inside a paddock, so both sources of
variation are present in the file:

- `set_stocking` points run 1021 to 2077 kg DM/ha; heights run 3.0 to 10.3 cm.
- `fast_rotation` points run 1735 to 3300 kg DM/ha; heights run 7.0 to 16.6 cm.

Within a single paddock the ten points still differ a good deal, which is the patchiness of an
upland sward. Paddocks also sit at different overall levels, reflecting aspect and drainage.

## Missing data

There are none. Every one of the 160 rows has a value in all five columns.

## How the file was produced

`make_data.py` generates `herbage_mass.csv` with a fixed random seed (20260822) and the Python
standard library only, so re-running it reproduces the same file byte for byte.
