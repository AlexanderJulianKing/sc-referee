# Data description

File: `ostrich_chick_grower_trial.csv`

## What one row represents

One row is one ostrich chick. Sixty-four individually identified chicks were reared on a
commercial farm to 90 days of age, 32 on each of two grower rations, and each chick was
measured once at the end of the rearing period. The file has 64 data rows plus a header
row. Every chick has a value in every outcome column, so there are no blank cells.

## Columns

Columns appear in this order. The eight outcome columns follow the order declared in the
trial protocol.

| # | Column | Meaning | Unit |
|---|--------|---------|------|
| 1 | `bird_id` | Identifier of the individual chick, `OS001` through `OS064`, unique within the file | none (identifier) |
| 2 | `diet_group` | Rearing diet the chick was allocated to. Exactly two distinct values: `standard` for the farm's standard grower ration, `lucerne_enriched` for the lucerne-enriched, higher-fibre grower ration | none (group label) |
| 3 | `body_weight_kg` | Live body weight of the chick at 90 days of age | kilograms (kg) |
| 4 | `average_daily_gain_g_per_day` | Average daily live-weight gain over the rearing period | grams per day (g/day) |
| 5 | `feed_conversion_ratio` | Feed conversion ratio: kilograms of feed consumed per kilogram of live-weight gain. Lower means more efficient | none (kg feed per kg gain, a ratio) |
| 6 | `tibiotarsus_length_cm` | Length of the tibiotarsus, the main lower leg bone, measured at 90 days | centimetres (cm) |
| 7 | `hock_circumference_cm` | Circumference of the hock joint, measured at 90 days | centimetres (cm) |
| 8 | `serum_total_protein_g_per_l` | Total protein concentration in blood serum | grams per litre (g/L) |
| 9 | `serum_calcium_mmol_per_l` | Calcium concentration in blood serum | millimoles per litre (mmol/L) |
| 10 | `packed_cell_volume_percent` | Packed cell volume, the share of blood volume made up of red cells | percent (%) |

## Row order and grouping

Rows are shuffled, so the two diet groups are interleaved rather than blocked. Group
membership is read from `diet_group`, not from row position.

## Provenance

The measurements are invented for this project, not collected from real birds. They were
produced by `make_data.py` in this directory with a fixed random seed, so rerunning that
script reproduces the same file. Values were drawn per bird from group-specific
distributions and clipped to plausible physiological limits, with a shared bird-level frame
factor linking the size-related outcomes so that heavier chicks also tend to show faster
gain, longer tibiotarsus and thicker hock.
