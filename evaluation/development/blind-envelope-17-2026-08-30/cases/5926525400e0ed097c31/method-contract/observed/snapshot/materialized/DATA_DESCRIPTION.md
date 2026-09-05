# Data description

File: `cane_ripener_trial.csv`

## What one row represents

One row is one individually tagged sugarcane stool, cut and analysed on its own at
harvest. There are 96 rows, one for each stool in the trial, plus a header row.
All 96 stools were of a single variety and stood in one uniform field of the same
plant crop age. Every stool has a value in every column: there are no missing
cells, no repeated stools, and no extra rows.

## Design counts held in the file

- Ripener condition: 48 stools `ripened`, 48 stools `untreated`.
- Study half: 48 stools `discovery`, 48 stools `validation`. The halves were drawn
  at random and written into the field book before any measurement was taken.
- The two splits are crossed and balanced: 24 stools in each of the four
  condition-by-half cells (ripened/discovery, ripened/validation,
  untreated/discovery, untreated/validation).

## Columns

The header uses these nine names, in this order.

| Column | Type | Values / unit | Meaning |
| --- | --- | --- | --- |
| `stool_id` | text | `ST001` through `ST096` | Stool tag: prefix `ST` plus a zero-padded three-digit serial number. Unique for every row. |
| `treatment` | text | exactly two values: `ripened`, `untreated` | Group column. The ripener condition. `ripened` stools received the chemical ripener applied six weeks before harvest; `untreated` stools received no application. |
| `study_half` | text | exactly two values: `discovery`, `validation` | Which pre-assigned study half the stool belongs to. Assigned at random before measurement and recorded in the field book. |
| `stalk_height_cm` | number | centimetres, whole numbers | Declared outcome 1. Millable stalk height. |
| `stalk_fresh_mass_kg` | number | kilograms per stalk, 2 decimals | Declared outcome 2. Stalk fresh mass. |
| `soluble_solids_brix` | number | degrees Brix, 1 decimal | Declared outcome 3. Juice soluble solids. |
| `juice_purity_pct` | number | percent, 1 decimal | Declared outcome 4. Juice purity. |
| `fibre_pct` | number | percent of fresh cane mass, 1 decimal | Declared outcome 5. Fibre content. |
| `recoverable_sugar_kg_per_t` | number | kilograms per tonne of cane, 1 decimal | Declared outcome 6. Estimated recoverable sugar. |

The six outcome columns appear in the declared outcome order fixed in the trial
plan before harvest. Each is rounded to the number of decimal places a cane
quality laboratory would report for that quantity.

## Provenance

The values are fixed and committed in the CSV; nothing is generated when the
analysis runs. `generate_data.py` in this directory is the one-off authoring
script that produced the file (fixed seed 20260830) and is kept only as a record
of how the file was made.
