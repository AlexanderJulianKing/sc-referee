# Data description: `starter_ph_readings.csv`

## What the file holds

Bench records from a sourdough starter maturation run. Twelve starter jars were built
from scratch on the same bench on the same day, fed on the same daily schedule, and held
at the same temperature. Six jars were fed a wholemeal rye flour and six were fed a
refined white wheat flour. The pH of every jar was read once a day, at the same time each
day, on six consecutive days of maturation.

## What one row represents

One row is **one jar on one day**: a single daily pH reading taken from a single starter jar.

## Units and row count

- Experimental units: **12 starter jars**
- Groups: **2 flour types**, 6 jars each
  - `wholemeal_rye` — 6 jars (`jar_01` through `jar_06`)
  - `refined_white_wheat` — 6 jars (`jar_07` through `jar_12`)
- Time points: **6 maturation days** (day 1 through day 6), one reading per jar per day
- Rows: **72** (12 jars x 6 days), plus one header line
- Columns: **4**

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `jar_id` | text | Label of the starter jar the reading came from. Twelve values, `jar_01` to `jar_12`. Each jar contributes 6 rows, one per maturation day. |
| `flour_type` | text | Flour the jar was fed for the whole run. Two values: `wholemeal_rye` and `refined_white_wheat`. Constant within a jar. |
| `maturation_day` | integer | Day of maturation on which the reading was taken. Values 1 through 6, where day 1 is the first daily reading after the jars were built. |
| `starter_ph` | number | The pH reading of that jar on that day, recorded to two decimal places. This is the study outcome. Values in this file run from 3.58 to 5.80. |

## Shape of the values

Both flours begin near pH 5.6 on day 1 and acidify over the run. Rye-fed jars settle
near pH 3.6 by day 6; wheat-fed jars settle near pH 3.9. Day-to-day scatter within a jar
is about 0.08 pH units, and jars sit about 0.12 pH units apart from one another on top of
that.

## How the file was made

`make_data.py` (Python standard library only, fixed random seed `20260823`) writes
`starter_ph_readings.csv`. Re-running it reproduces the file byte for byte. The CSV is
stored as plain text and is the input to the analysis; nothing is regenerated at analysis
time.
