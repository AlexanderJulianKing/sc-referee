# Data description

## File

`biofilm_coupons.csv` — one CSV with a header row and 44 data rows.

## What one row represents

One row is one sterile silicone catheter coupon. Each coupon was incubated on
its own in an identical flow cell, with the same reference bacterial strain and
the same artificial urine medium, for 48 hours. It was then removed and
measured for all four declared biofilm outcomes. So a row holds the complete
outcome family for a single coupon, and no coupon appears twice.

The 44 coupons split into 22 uncoated and 22 hydrophilic-coated. Every cell is
filled; there are no blanks.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `coupon_id` | text | — | Coupon label, `CP-01` through `CP-44`. Unique per row. |
| `surface` | text | — | Group. Exactly two values: `uncoated` or `hydrophilic`. |
| `biofilm_od590` | number | optical density at 590 nm | Declared outcome 1. Biofilm biomass by crystal violet staining. Recorded to 3 decimals. |
| `viable_log10_cfu_per_cm2` | number | log10 CFU per cm^2 | Declared outcome 2. Viable cells recovered from the coupon surface. Recorded to 2 decimals. |
| `thickness_um` | number | micrometres | Declared outcome 3. Mean biofilm thickness by confocal imaging. Recorded to 1 decimal. |
| `eps_protein_ug_per_cm2` | number | micrograms per cm^2 | Declared outcome 4. Extracellular polymeric substance protein on the coupon. Recorded to 1 decimal. |

Outcome columns appear in the declared order: biomass, viable counts,
thickness, EPS protein.

## Notes

- Decimals reflect how each instrument reports: the plate reader to 3 decimals,
  plate counts to 2, confocal thickness and the protein assay to 1.
- Coupons were prepared and numbered as one batch, then assigned to a surface,
  so the two groups are interleaved through the `coupon_id` sequence rather
  than blocked.
