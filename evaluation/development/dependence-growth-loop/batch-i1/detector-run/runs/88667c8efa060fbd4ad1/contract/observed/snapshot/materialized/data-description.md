# Boreal fen drainage experiment: chamber methane flux sessions

Each line of `data/input.csv` records one static-chamber methane flux session carried out at one permanent collar in a boreal fen. Twelve collars were installed, six in intact peat and six inside an experimental drainage block, and every collar was visited in three seasonal sessions (early summer, midsummer, late summer), which gives 36 lines in total.

One row is: one seasonal chamber flux session measured at one permanent collar
Independent unit column: collar_id

Columns:

- `collar_id` - identifier of the permanent chamber collar. The same collar appears on three lines, once per session.
- `treatment` - water-table treatment of the collar, either `intact` or `drained`. It is a property of the collar and is fixed across all of that collar's sessions.
- `session` - seasonal visit number, 1 to 3, in chronological order within a collar.
- `water_table_depth_cm` - depth of the water table below the peat surface at the moment of the session, in centimetres. Larger numbers mean a drier profile.
- `ch4_flux_mg_m2_h` - methane flux measured by the chamber, in milligrams of CH4 per square metre per hour.

Because the three sessions of a collar are repeated measurements of the same physical plot, they are not independent of one another: they share the collar's peat depth, vegetation and microtopography. A treatment comparison should use a single value per collar, and the analysis averages a collar's sessions before testing, so the twelve collars are the values that enter the test.
