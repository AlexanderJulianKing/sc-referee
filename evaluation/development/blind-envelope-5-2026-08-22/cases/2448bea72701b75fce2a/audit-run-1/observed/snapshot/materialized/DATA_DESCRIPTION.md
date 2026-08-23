# Data description

## File

`classroom_co2.csv` — one comma-separated data file, with a header line and 80 data rows.

## What one row is

One row is **one logged classroom**: a single carbon dioxide logger sitting in one occupied
classroom in one school building on one cold weekday. A row is not a building and not a pupil.

## Units in the file

- **16 school buildings** took part. These are the units that received or did not receive the
  ventilation upgrade; the upgrade was installed building-wide, so every classroom inside a
  building shares that building's ventilation status.
- **5 logged classrooms per building**, spread across floors and wings.
- **80 classroom records** in total (16 x 5), which is the number of rows in the file.

## The two groups

| Group | `ventilation_status` value | Buildings | Classroom rows |
|---|---|---|---|
| Buildings that received the ventilation upgrade | `upgraded` | 8 | 40 |
| Comparable buildings that kept their original ventilation | `unupgraded` | 8 | 40 |

## Columns

Columns appear in this order.

| # | Column | Type | Description |
|---|---|---|---|
| 1 | `building_ref` | text | Estate-management reference for the school building, in the form `EDU/<district code>/<asset number>`, e.g. `EDU/CE/0865`. There are 16 distinct values, each appearing on exactly 5 rows. This is the building identifier, so it is also the grouping label that says which rows come from the same building. |
| 2 | `ventilation_status` | text | Whether that building has the upgraded ventilation. Two possible values: `upgraded` or `unupgraded`. Constant within a building, because the upgrade was installed building-wide. |
| 3 | `room_label` | text | The classroom's name as the school uses it, e.g. `Y4 Willow`, `Y2 Juniper`, `Room 3A`. Labels are unique within a building but can repeat across different buildings. |
| 4 | `pupils_present` | integer | Number of pupils in that room while the logger was recording. Range 18 to 32. |
| 5 | `mean_co2_ppm` | integer | The outcome. Mean mid-lesson carbon dioxide concentration in the room, in parts per million, rounded to whole ppm. Roughly 1200 to 2100 in unupgraded buildings and roughly 750 to 1350 in upgraded buildings. |

## Notes on the values

Concentrations carry a strong building-level signature: rooms inside the same building sit close to
that building's own baseline, which stands in for its age, airtightness and boiler schedule.
Room-to-room variation inside a building is smaller than the spread between buildings. Fuller rooms
run a little higher than emptier rooms in the same building.

## How the file was produced

`make_data.py` (Python standard library only, fixed random seed `20260822`). Re-running it
regenerates `classroom_co2.csv` identically.
