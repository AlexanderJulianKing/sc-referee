# Data description

## Files

There is one data file: `breakfast_glucose_mornings.csv`. The study calls for a single
comma-separated data file, so no second summary file was created.

`make_data.py` is the generator that produced it (Python standard library only, fixed seed
`20260822`). Re-running it rewrites the same file byte-for-byte.

## What one row represents

One row is **one volunteer on one study morning**: a single breakfast, eaten at home, and the
glucose values recorded around it. A row is *not* a person and *not* a summary of a person. Each
volunteer appears on 14 separate rows, one per consecutive study morning.

## Counts

| Level | Count |
|---|---|
| Volunteers (independent units randomised) | 24 |
| Volunteers per arm | 12 and 12 |
| Mornings per volunteer | 14 |
| Data rows (person-mornings) | 336 |
| Rows per arm | 168 and 168 |
| Header lines | 1 |
| Missing cells | 0 |

336 = 24 volunteers x 14 mornings. The file has 337 lines in total: 1 header plus 336 data rows.

## The two groups

Volunteers were randomised as whole people. Whichever arm a volunteer is in, they stay in it for
all 14 of their mornings, so `breakfast_arm` never changes within a `volunteer_code`.

| `breakfast_arm` value | Meaning | Volunteers | Rows |
|---|---|---|---|
| `refined_cereal` | Refined-cereal breakfast (comparison) | 12 | 168 |
| `high_protein` | High-protein breakfast (intervention) | 12 | 168 |

Arm membership by volunteer code:

- `refined_cereal`: PDB-102, PDB-103, PDB-106, PDB-107, PDB-108, PDB-110, PDB-112, PDB-113,
  PDB-115, PDB-118, PDB-121, PDB-124
- `high_protein`: PDB-101, PDB-104, PDB-105, PDB-109, PDB-111, PDB-114, PDB-116, PDB-117,
  PDB-119, PDB-120, PDB-122, PDB-123

## Columns

Columns appear in this order, with these exact headers.

| # | Column | Type | Values in this file | Meaning |
|---|---|---|---|---|
| 1 | `volunteer_code` | text | 24 distinct codes, `PDB-101` to `PDB-124` | Anonymised participant label. Identifies the person. Repeats on 14 rows, one per morning. |
| 2 | `breakfast_arm` | text | `refined_cereal`, `high_protein` | Randomised breakfast assignment. Fixed for a volunteer across all 14 of their rows. |
| 3 | `study_day` | integer | 1 to 14 | Which of the 14 consecutive study mornings this row records, for that volunteer. |
| 4 | `fasting_glucose_mmol_l` | decimal, 1 dp | 5.2 to 6.9 | Fasting blood glucose that morning, before the breakfast, in mmol/L. |
| 5 | `peak_glucose_mmol_l` | decimal, 1 dp | 6.8 to 10.4 | Outcome. Highest glucose reached in the two hours after that morning's breakfast, from the continuous glucose sensor, in mmol/L. |

Glucose values are rounded to one decimal place. Rows are sorted by `volunteer_code`, then by
`study_day`.

## How the values were built

The generator gives every volunteer a persistent personal level that applies to all 14 of their
mornings, then adds independent day-to-day noise on top of it for each morning. So the 14 rows
belonging to one volunteer are not independent of each other: they share that person's level.
In the file as generated, roughly 40 to 46 percent of the variation in `peak_glucose_mmol_l`
within an arm sits between volunteers rather than between mornings of the same volunteer.

Fasting glucose is generated the same way (a personal level plus daily noise) and does not depend
on `breakfast_arm`, because the fasting reading is taken before the meal is eaten.

Values that fell outside physiologically plausible limits were redrawn rather than clipped to the
limit, so no value piles up on a boundary.
