# Data description

## File

`gari_fermentation_batches.csv` — 40 data rows plus one header row.

## What one row represents

One row is one fermentation batch: a single 20 kg unit of grated cassava mash fermented in its own
press bag and sampled once, 72 hours after fermentation started. Each batch is measured once, so
there is one row per batch and no repeated measures. Twenty batches were run with a back-slopped
inoculum carried over from a previous successful batch, and twenty were left to ferment
spontaneously with no added inoculum.

## Columns

| Column | Meaning | Unit |
| --- | --- | --- |
| `batch_id` | Batch identifier, unique across the study. `BS-01` … `BS-20` are the back-slopped batches, `SP-01` … `SP-20` the spontaneous ones. | none (text label) |
| `fermentation_treatment` | Group assignment. Exactly two values: `back_slopped` for the back-slopped inoculum, `spontaneous` for fermentation with no added inoculum. | none (category) |
| `total_cyanogenic_potential_mg_hcn_eq_per_kg_dw` | Declared outcome 1. Total cyanogenic potential of the finished gari. | milligrams hydrogen cyanide equivalent per kilogram dry weight |
| `ph_72h_ph_units` | Declared outcome 2. pH of the mash measured at 72 hours. | pH units |
| `titratable_acidity_percent_lactic_acid` | Declared outcome 3. Titratable acidity of the mash at 72 hours, expressed as lactic acid. | percent lactic acid (g lactic acid per 100 g) |
| `moisture_content_percent` | Declared outcome 4. Moisture content of the finished gari. | percent by mass |

The outcome columns appear in the order the four outcomes were declared in the study plan.

## Completeness

Every batch has a value in every outcome column. There are no blank cells and no missing-value
codes. All 40 `batch_id` values are distinct, and the group column holds exactly the two values
listed above, 20 rows each.

## Provenance

The measurements are invented for this project, not collected from a real processing run. They were
produced by `generate_data.py` in this directory, which draws each outcome from a normal
distribution clipped to a plausible measurement window for artisanal cassava processing. The
generator uses a fixed random seed, so the CSV can be regenerated exactly.
