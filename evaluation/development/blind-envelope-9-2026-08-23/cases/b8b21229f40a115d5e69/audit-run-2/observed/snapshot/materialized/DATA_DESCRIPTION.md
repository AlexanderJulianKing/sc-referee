# Data description

## File

`squirrel_liver_lead.csv` — the single data file for the study. Comma-separated,
one header line followed by 78 data rows.

It is produced by `make_data.py` (Python standard library only, fixed random
seed `20260824`). Re-running that script reproduces the file exactly.

## What one row represents

One row is **one instrument reading**: a single digestion and measurement of one
squirrel's liver homogenate on one analytical run.

A row is not a squirrel. Each squirrel's liver was freeze-dried and homogenised
once, and that one homogenate was digested and read three separate times on the
same instrument. So each animal supplies three rows, which differ from one
another only by analytical error.

## Units and counts

| Quantity | Count |
| --- | --- |
| Squirrels (carcasses) | 26 |
| Analytical runs per squirrel | 3 |
| Data rows | 78 |
| Homogenates per squirrel | 1 |

## The two groups

The 26 animals came from routine culls in two collection settings, 13 animals in
each:

| `collection_setting` value | Meaning | Squirrels | Rows |
| --- | --- | --- | --- |
| `urban_park` | Inner-city parks | 13 | 39 |
| `rural_woodland` | Rural woodland | 13 | 39 |

Tags `SQ-101` through `SQ-113` are the urban park animals; `SQ-114` through
`SQ-126` are the rural woodland animals.

## Columns

The file has four columns, in this order.

| Column | Type | Description |
| --- | --- | --- |
| `squirrel_tag` | text | Carcass tag code identifying the individual animal, in the form `SQ-101` upward through `SQ-126`. This is the unit column: it names the squirrel a reading came from. Each of the 26 codes appears on exactly 3 rows. |
| `collection_setting` | text | Where the animal was collected. Two values only: `urban_park` (inner-city parks) or `rural_woodland` (rural woodland). Constant across all three rows of a given squirrel, because setting is a property of the animal. |
| `analytical_run` | integer | Which of the three analytical replicates on that animal's homogenate this reading is: `1`, `2`, or `3`. Numbering is within an animal, so the value repeats across animals and carries no meaning between them. |
| `lead_mg_per_kg_dw` | decimal number | Measured hepatic lead concentration for that reading, in milligrams of lead per kilogram of liver dry weight. Reported to four decimal places. |

## Observed values

Across all 78 rows, `lead_mg_per_kg_dw` runs from 0.048 to 0.660 mg/kg dry
weight. By group:

| Group | Rows | Mean | SD | Min | Max |
| --- | --- | --- | --- | --- | --- |
| `urban_park` | 39 | 0.365 | 0.125 | 0.191 | 0.660 |
| `rural_woodland` | 39 | 0.126 | 0.055 | 0.048 | 0.214 |

Averaged to one value per animal, the 26 animal means span 0.050 to 0.654 mg/kg
dry weight, with a standard deviation of 0.156 across animals.

The three readings from a single homogenate agree closely: the within-animal
coefficient of variation averages 2.4% and never exceeds 4.8%. Animals differ
from one another far more than the three readings on any one animal differ from
each other.

## How the values were generated

`make_data.py` draws one true homogenate concentration per animal from a
lognormal distribution centred on the group's level (median 0.365 mg/kg for
urban park animals, 0.118 mg/kg for rural woodland animals), redrawing any value
that falls outside the plausible range 0.040 to 0.700 mg/kg. Each of the three
readings for that animal is then that true value multiplied by a small lognormal
instrument error with a coefficient of variation of about 3%.
