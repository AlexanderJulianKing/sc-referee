# Data description: street tree sap flow by planting pit design

## Files

- `sap_flow.csv` — the single data file for this study.
- `make_data.py` — the script that produced `sap_flow.csv` (fixed random seed
  `20260823`, Python standard library only). The CSV is committed as plain text
  and is not regenerated at analysis time.

This brief calls for one data table, so there is no second summary CSV.

## What one row represents

One row is **one tree in one month**: the mean daily sap flow recorded for a
single street tree during the settled mid-month measurement week of a single
month of the growing season.

## Units and counts

- **Independent units:** 20 street trees, all the same species and the same
  nursery stock, planted along comparable roads in one city.
- **Measurements per tree:** 6 (one per month, April through September).
- **Rows in the CSV:** 120 data rows, plus one header row.
- **Tree identifiers:** `T01` through `T20`, each appearing exactly 6 times.
- The design is balanced: every tree has all six months, and no values are
  missing.

## The two groups

| `pit_design` value | Meaning | Trees | Rows |
| --- | --- | --- | --- |
| `conventional` | Conventional compacted planting pit (the standard street specification) | 10 (`T01`–`T10`) | 60 |
| `structural_soil` | Engineered structural-soil pit, built to hold more water | 10 (`T11`–`T20`) | 60 |

Planting pit design is a property of the tree, not of the month, so it is
constant across all six rows belonging to a given tree.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `tree_id` | text | Identifier of the individual street tree, `T01`–`T20`. This is the independent unit; the six rows sharing a `tree_id` are repeated measures on the same tree. |
| `pit_design` | text (2 levels) | Planting pit design for that tree: `conventional` or `structural_soil`. Fixed for the life of the tree. |
| `measurement_month` | text (6 levels) | Calendar month of the measurement week: `April`, `May`, `June`, `July`, `August`, `September`. Rows appear in this order within each tree. |
| `mean_daily_sap_flow_l_per_day` | number, 1 decimal place | Outcome. Mean daily sap flow over the mid-month measurement week, in litres per day. Recorded to 0.1 L/day, the resolution the sap flow loggers report. |

## Ranges and spread in the delivered file

- Observed sap flow runs from **4.0** to **28.5** L/day; all values are positive
  and lie inside the plausible sensor range of about 4 to 33 L/day.
- Group means: **13.8** L/day for `conventional`, **18.7** L/day for
  `structural_soil` (raw row-level averages, difference 4.9 L/day).
- A single tree moves about **2.8** L/day from month to month (mean of the
  within-tree standard deviations), reflecting weather and measurement noise.
- Trees differ from one another by about **4.7–4.9** L/day (standard deviation
  of the 20 tree means within each group), which is why the six readings from a
  tree cannot be treated as six independent observations.

## How the values were produced

`make_data.py` builds each value as a planting-pit mean (14 L/day conventional,
19 L/day structural soil) plus a tree-level offset (spread about 4 L/day), plus
a month effect shared by every tree in the city (the common weather swing), plus
independent per-reading measurement noise. The month effects and tree offsets
are centred and rescaled to their target spread so the group means land on their
intended values. Results are clipped to 4–33 L/day and rounded to 0.1 L/day.
One value was clipped at the 4.0 L/day floor.
