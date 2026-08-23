# Data description

## File

`alpaca_fibre.csv` — the single data table for the trial. 80 data rows plus one header row.

## What one row represents

One row is **one mid-side fibre sample taken from one alpaca in one calendar month**, together with
the animal's age and its body weight recorded at that sampling.

## Units and coverage

- 20 adult huacaya alpacas, identified `ALP01` through `ALP20`.
- 4 consecutive monthly samplings per animal: `2026-03`, `2026-04`, `2026-05`, `2026-06`.
- 20 animals x 4 months = 80 rows. Every animal contributes exactly 4 rows, one per month, and the
  four rows for an animal are successive samplings of that same individual. The table is complete;
  there are no missing cells.

## The two groups

| `diet_group` | Ration | Animals | Rows |
| --- | --- | --- | --- |
| `supplemented` | Daily ration plus the trace-mineral supplement | 10 (`ALP02`, `ALP04`, ... `ALP20`) | 40 |
| `unsupplemented` | Daily ration without the supplement | 10 (`ALP01`, `ALP03`, ... `ALP19`) | 40 |

Group assignment is fixed for an animal: an alpaca is in the same `diet_group` in all four of its rows.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `alpaca_id` | text | — | Animal identifier, `ALP01`–`ALP20`. Repeats 4 times, once per monthly sampling. |
| `diet_group` | text | — | Ration the animal received: `supplemented` or `unsupplemented`. Constant within an animal. |
| `sampling_month` | text | — | Calendar month of the sampling, `YYYY-MM`. One of `2026-03`, `2026-04`, `2026-05`, `2026-06`. |
| `fibre_diameter_um` | number | micrometres (um) | Mean fibre diameter of that month's mid-side sample, rounded to 2 decimals. |
| `age_years` | integer | years | Age of the animal in whole years, 2–11. Constant within an animal. |
| `body_weight_kg` | number | kilograms | Body weight recorded at that sampling, rounded to 1 decimal. Varies month to month. |

## Observed ranges in the delivered file

| Column | Range |
| --- | --- |
| `fibre_diameter_um` | 21.63 to 29.93 |
| `age_years` | 2 to 11 |
| `body_weight_kg` | 56.4 to 84.9 |

Group mean fibre diameter across all rows: unsupplemented 26.55 um, supplemented 24.57 um.

## Provenance

Values are simulated, not measured. `make_data.py` (Python standard library only, fixed seed
`20260847`) produces `alpaca_fibre.csv` and reproduces it byte for byte on re-run. Fibre diameter is
drawn as a group mean (26.5 um unsupplemented, 24.5 um supplemented) plus a persistent per-animal
offset (SD 1.8 um) plus a monthly draw within the animal (SD 0.8 um), clipped to 19–31 um. Body
weight starts from a level that rises gently with age and drifts slowly across the four months.
