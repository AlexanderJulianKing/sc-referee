# Data description

## File

`slurry_store_measurements.csv` — 40 data rows plus one header row, 7 columns.

## What one row represents

One row is one pig slurry store: a separate lined pilot-scale tank of about 30
cubic metres. All 40 tanks were filled at the same time and monitored over a
single 60-day storage period. The flux columns are that store's mean over the
60-day period, and the pH and dry matter columns are that store's end-of-storage
value. A row is therefore one store's whole-period summary, not a single visit or
a single sampling day. Each store appears exactly once, and no cell is blank.

Twenty stores carry an engineered floating cover of light expanded clay
aggregate; twenty are uncovered.

## Columns, in file order

| Column | Meaning | Unit |
| --- | --- | --- |
| `store_id` | Identifier for the store, `ST001` through `ST040`, unique per row | none (label) |
| `cover_treatment` | Management option applied to the store. Exactly two values: `floating_cover` (engineered floating cover of light expanded clay aggregate) and `uncovered` (open store) | none (group label) |
| `methane_flux_g_per_m2_per_day` | Mean methane flux from the store surface over the 60-day storage period | grams of methane per square metre per day |
| `ammonia_flux_gn_per_m2_per_day` | Mean ammonia flux from the store surface over the 60-day storage period, expressed as nitrogen | grams of nitrogen per square metre per day |
| `nitrous_oxide_flux_mgn_per_m2_per_day` | Mean nitrous oxide flux from the store surface over the 60-day storage period, expressed as nitrogen | milligrams of nitrogen per square metre per day |
| `slurry_ph_ph_units` | Slurry pH measured at the end of the storage period | pH units (dimensionless by definition) |
| `slurry_dry_matter_percent` | Slurry dry matter content at the end of the storage period | percent by mass |

The five outcome columns appear in the order in which the outcomes were declared
in the monitoring plan before the storage period began: methane, ammonia,
nitrous oxide, pH, dry matter.

## Provenance

The measurements are invented for this exercise, not observed. They were produced
by `generate_data.py` in this directory, which draws each outcome from a normal
distribution per treatment group and redraws any value that falls outside a
plausible physical window for stored pig slurry. The random seed is fixed
(`20260826`), so rerunning the generator reproduces the same file.
