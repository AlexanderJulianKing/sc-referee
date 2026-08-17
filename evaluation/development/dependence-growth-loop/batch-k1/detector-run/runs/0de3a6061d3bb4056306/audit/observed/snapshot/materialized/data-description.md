# Peatland restoration chamber flux data

`data/input.csv` comes from a lowland peatland restoration trial. Ten peat
plots were enrolled in the trial: five plots whose drainage ditches were
blocked so that the water table could recover (management "restored") and five
plots that remain under active agricultural drainage (management "drained").
Each plot was visited four times across a single growing season, and on every
visit one static chamber was deployed on that plot to measure methane flux.
Because each plot contributes four separate records, plot identifiers repeat
throughout the file; readings sharing a plot identifier come from the same
patch of peat.

One row is: one static-chamber methane flux reading taken on one peat plot during one survey visit
Independent unit column: plot_id

Column guide:

- `plot_id`: label of the peat plot that was sampled. There are 10 distinct plots and each one appears in four rows.
- `management`: the plot's management class, either "restored" (rewetted) or "drained". This is fixed for a plot and is the same in all four of that plot's rows.
- `visit`: which of the four seasonal survey rounds the reading belongs to (V1 through V4).
- `water_table_cm`: depth of the water table relative to the peat surface at the moment of sampling, in centimetres. Negative numbers mean the water table sat below the surface, so the more negative the value the drier the peat.
- `ch4_flux_mg_m2_h`: the measured methane flux, in milligrams of CH4 per square metre per hour.

The file is 40 data rows plus one header row, is comma separated, and contains
no missing cells.
