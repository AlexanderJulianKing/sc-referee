# What is in data/input.csv

This is a field survey of ten restored hillside terraces in the Kalu catchment,
recorded after two wet seasons. Five of the terraces had been treated with a
biochar topsoil amendment when they were built; the other five were left
unamended. On every terrace the survey crew measured steady-state infiltration
with a double-ring infiltrometer at four permanently marked sampling plots, so
each terrace contributes four rows to the file.

Columns:

- `terrace_id` - label of the restored terrace that the sampling plot sits on,
  running from TR-01 to TR-10. Each label appears four times.
- `treatment` - `biochar` if that terrace received the topsoil amendment,
  `none` if it did not. The treatment was applied to whole terraces, so this
  value is the same for all four plots on a terrace.
- `plot_code` - which of the four marked sampling plots on that terrace was
  read (P1 to P4).
- `infiltration_mm_per_h` - the steady-state infiltration rate at that plot, in
  millimetres per hour.

One row is: one double-ring infiltrometer reading taken at one marked sampling plot on one terrace
Independent unit column: terrace_id
