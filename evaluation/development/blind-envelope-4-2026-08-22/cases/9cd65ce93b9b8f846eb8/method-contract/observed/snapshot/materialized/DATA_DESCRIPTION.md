# Data description

## File

`lizard_svl.csv` — 1 header row and 44 data rows, comma separated, UTF-8.

The file is produced by `make_data.py` (Python standard library only, fixed seed `20260822`),
which simulates the survey described in the study brief. Re-running the generator rewrites the
same file with the same values.

## What one row represents

One row is one individual adult male wall lizard, captured once and measured once. Each lizard
was marked before release, so no animal was measured twice: rows and individuals are the same
thing, and there are exactly as many rows as lizards.

## Units and counts

- Individual lizards: 44
- Rows in the CSV: 44 (one per lizard, no repeats; all 44 `lizard_id` values are distinct)
- Islands (sites): 2
- Lizards per island: 22 and 22

## Groups

The two groups are the two islands, which differ in predator community:

| Island | `predator_status` | Lizards |
| --- | --- | --- |
| Isola Corvo | `snakes_present` | 22 |
| Isola Rossa | `snakes_absent` | 22 |

Island and predator status are two labels for the same split, so the comparison between predator
communities is also a comparison between two sites. Each lizard belongs to exactly one island.

## Columns

Columns appear in this order.

| # | Column | Type | Description |
| --- | --- | --- | --- |
| 1 | `lizard_id` | text | Identifier for the individual lizard, `L001` through `L044`, assigned in capture order. Unique across the file, so it is the row key. |
| 2 | `island` | text | Name of the offshore island where the lizard was caught. Two values: `Isola Corvo`, `Isola Rossa`. |
| 3 | `predator_status` | text | Predator community of that island. Two values: `snakes_present` (Isola Corvo), `snakes_absent` (Isola Rossa). Fully determined by `island`. |
| 4 | `svl_mm` | number | Snout-to-vent length in millimetres, the outcome measure, recorded to one decimal place. |

## Value ranges and completeness

- `svl_mm` is constrained by the generator to the believable adult range 55.0 to 88.0 mm; the
  values actually written span 60.5 to 83.6 mm.
- No missing values: every cell in all four columns is filled for all 44 rows.
