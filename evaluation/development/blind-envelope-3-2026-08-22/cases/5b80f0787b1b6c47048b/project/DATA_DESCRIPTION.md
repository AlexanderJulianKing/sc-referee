# Data description

## File

`ewe_weaning_weights.csv` — one comma-separated file, a header row plus 44 data rows.
It is the only data file in the project. The values are invented for this exercise and were
produced by `make_data.py` (Python standard library only, fixed seed 20260821); re-running that
script rewrites the same file.

## What one row represents

One row is one ewe, recorded once at weaning. Each of the 44 ewes appears in the file exactly once,
so the 44 rows are 44 distinct animals and the 44 `ewe_id` values are all different. There are no
repeated measurements, no lamb-level rows, and no before-and-after records. The row is therefore the
ewe, and the ewe is the experimental unit.

## Units and groups

Forty-four ewes on a single hill farm, split into two treatment groups of equal size:

| Group | `treatment` value | Ewes (rows) |
| --- | --- | --- |
| Mineral drench six weeks before lambing | `drenched` | 22 |
| No drench | `undrenched` | 22 |

Each ewe belongs to one group only. Group membership does not change during the trial, so the
comparison between groups is a comparison between two independent sets of animals.

## Columns

All six columns are present for all 44 rows; there are no missing values.

| Column | Type | Values in the file | Meaning |
| --- | --- | --- | --- |
| `ewe_id` | text | `E001`–`E022` (drenched), `E101`–`E122` (undrenched) | Unique identifier for the ewe. Appears once and only once in the file. |
| `treatment` | text | `drenched`, `undrenched` | Whether the ewe received the pre-lambing mineral drench. |
| `lambs_weaned` | integer | 1 or 2 | Number of lambs that ewe weaned. 15 drenched and 14 undrenched ewes weaned twins; the rest weaned singles. |
| `ewe_age_years` | integer | 2 to 6 | Age of the ewe in years at lambing. |
| `body_condition_score` | number | 1.5 to 4.5 in half-point steps | Body condition score of the ewe at mating, on the usual five-point scale. |
| `total_weaned_lamb_weight_kg` | number, one decimal | 25.1 to 56.0 | Outcome. Combined weight in kilograms of all lambs that ewe weaned. For a twin-rearing ewe this is the sum of both lambs. |

## Summary of the outcome

| Group | Ewes | Mean total weaned lamb weight (kg) | Standard deviation (kg) | Range (kg) |
| --- | --- | --- | --- | --- |
| `drenched` | 22 | 41.5 | 6.6 | 28.9–56.0 |
| `undrenched` | 22 | 37.8 | 6.4 | 25.1–50.0 |

The spread quoted here is the standard deviation among ewes within a group.
