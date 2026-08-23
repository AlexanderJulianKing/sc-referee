# Data description

## File

`termite_mound_soil_nitrogen.csv` — one comma-separated table, header row plus 112 data rows.

The file is produced by `make_data.py` (Python standard library only, fixed seed `20260823`).
Re-running `python3 make_data.py` overwrites the CSV with a byte-identical copy. The values are
invented for this exercise; they are not measurements from a real field campaign.

## What one row represents

**One row is one soil core.** Each row holds the total soil nitrogen measured in a single core,
together with the mound that core came from, where around the mound base it was taken, how deep it
went, and the soil pH of that core.

A row is *not* a mound. Eight rows share each mound.

## Units and counts

| Level | Count | Notes |
|---|---|---|
| Termite mounds sampled | 14 | `MND01` through `MND14` |
| Soil cores per mound | 8 | numbered 1–8 within each mound |
| Rows in the file | 112 | 14 mounds x 8 cores |

The mound is the independent unit of the study. The eight cores at a mound are spatial subsamples of
that same mound, so they are correlated with each other: they share the mound's own nitrogen level,
its height, and its local soil conditions. Treating the 112 rows as 112 independent observations
would overstate how much information the data actually carry.

## The two groups

The 14 mounds sit in two adjacent blocks, 7 mounds in each. Group membership is a property of the
mound, not of the core, so all 8 cores from a mound carry the same label.

| `burn_block` value | Mounds | Cores | Meaning |
|---|---|---|---|
| `burned` | 7 (`MND08`–`MND14`) | 56 | block subjected to a prescribed burn two years before sampling |
| `unburned` | 7 (`MND01`–`MND07`) | 56 | adjacent block with no prescribed burn |

The design is balanced: both groups have 7 mounds, and every mound has 8 cores.

## Columns

The file has 8 columns, in this order.

| # | Column | Type | Units | Varies at | Description |
|---|---|---|---|---|---|
| 1 | `mound_id` | text | — | mound | Mound identifier, `MND01`–`MND14`. Groups the 8 rows that belong to one mound. |
| 2 | `burn_block` | text | — | mound | Which block the mound sits in: `burned` or `unburned`. Constant across a mound's 8 rows. |
| 3 | `core_number` | integer | — | core | Which of the mound's 8 cores this row is, 1–8. A label only; it does not encode direction or order of collection, and the same number in two different mounds refers to two unrelated cores. |
| 4 | `total_nitrogen_pct` | decimal | percent by mass | core | Total soil nitrogen in the core. This is the outcome the study is about. Recorded to 3 decimal places. |
| 5 | `mound_height_m` | decimal | metres | mound | Height of the mound above the surrounding ground. Constant across a mound's 8 rows, so the file holds 14 distinct heights repeated 8 times each, not 112 independent heights. |
| 6 | `core_distance_cm` | decimal | centimetres | core | Distance from the mound base out to where the core was taken. |
| 7 | `sample_depth_cm` | integer | centimetres | core | Depth the core was taken to. One of three fixed depths: 10, 20, or 30 cm. |
| 8 | `soil_ph` | decimal | pH units | core | Soil pH measured in that core. Recorded to 2 decimal places. |

### Ranges in the generated file

| Column | Range in this file |
|---|---|
| `total_nitrogen_pct` | 0.064 to 0.303 |
| `mound_height_m` | 0.82 to 3.23 (14 distinct values) |
| `core_distance_cm` | 21.4 to 149.8 |
| `sample_depth_cm` | 10, 20, 30 |
| `soil_ph` | 6.48 to 8.09 |

## Missing values

There are none. Every one of the 112 rows has a value in all 8 columns.
