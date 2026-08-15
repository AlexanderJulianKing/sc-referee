# Sarvisuo mire ebullition survey

`data/input.csv` holds the field log from a single growing season on the
Sarvisuo mire, where methane ebullition was scored during static-chamber
closures on six permanent collars. Three collars sit in an intact fen section
and three sit in a block that was ditch-drained for forestry in the 1970s.
Each collar was revisited in survey weeks 24, 27 and 31; two collars were not
reachable in week 31, so those collars contribute two deployments instead of
three.

Columns:

- `deployment_id`: label for one chamber closure, unique across the file.
- `collar_id`: the permanent collar the chamber was seated on (FEN-* collars
  are intact, DRN-* collars are drained). The same collar appears in several
  rows of the file.
- `drainage_status`: `intact` or `drained`, a property of the collar's block
  rather than of the individual visit.
- `survey_week`: ISO week number of the visit.
- `peat_temp_c`: peat temperature at 10 cm depth, degrees Celsius.
- `water_table_cm`: water table position relative to the peat surface, in
  centimetres (negative values are below the surface).
- `ebullition_detected`: `yes` if at least one bubble release was seen or
  logged during the closure, otherwise `no`.

One row is: one static-chamber closure on one permanent collar in one survey week
Independent unit column: collar_id
One trial is: one row
