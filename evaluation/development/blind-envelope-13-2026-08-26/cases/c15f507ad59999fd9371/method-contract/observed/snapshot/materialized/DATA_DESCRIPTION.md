# Data description

File: `rearing_trays.csv` (36 data rows plus one header row)

## What one row represents

One row is one rearing tray, that is one cohort of fifth-instar silkworm larvae fed exclusively on
a single mulberry cultivar and scored as a unit at spinning. The tray, not the individual larva, is
the unit of observation. Thirty-six trays were reared, 18 fed on each cultivar. Every tray has a
value in every outcome column; there are no blank cells.

## Columns

Columns appear in this order.

| Column | Meaning | Unit |
| --- | --- | --- |
| `tray_id` | Tray identifier, `T01` through `T36`, in rearing order. One row per identifier. | none (label) |
| `cultivar` | Mulberry cultivar fed to that tray. Exactly two distinct values: `V1` and `S36`. This is the group column. | none (label) |
| `mean_cocoon_weight_g` | Mean weight of a single cocoon for the tray, first declared outcome. | grams |
| `cocoon_shell_ratio_pct` | Cocoon shell ratio for the tray, shell weight as a share of whole cocoon weight, second declared outcome. | percent |
| `larval_duration_h` | Fifth-instar larval duration for the tray, from brushing into the fifth instar to spinning, third declared outcome. | hours |
| `silk_filament_length_m` | Silk filament length reeled per cocoon for the tray, fourth declared outcome. | metres |
| `effective_rearing_rate_pct` | Effective rate of rearing, the share of brushed larvae yielding good cocoons, fifth declared outcome. | percent |

The five outcome columns appear in the order the trial protocol declared them.

## Provenance

The values are invented for this project, not measured. They were produced by `make_data.py` in this
directory with a fixed random seed, drawing each outcome from a per-cultivar normal distribution
with commercial bivoltine centres and spreads, clipping to plausible physical ranges, and rounding
to field-record precision (2 decimals for cocoon weight, 1 decimal for shell ratio, larval duration
and effective rearing rate, whole metres for filament length).
