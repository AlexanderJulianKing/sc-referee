# What data/input.csv contains

This file comes from a survey of fungal mycelial ingrowth in a montane Norway
spruce landscape. Twenty-four stands were selected across the survey area, each
at least two kilometres from the nearest other stand and each sitting on its own
soil block, so the stands are treated as independent of one another.

In every stand, four nylon-mesh ingrowth bags filled with acid-washed sand were
buried in the organic horizon in June and lifted in September. The four bags
from a stand were combined into a single composite sample in the field, and that
one composite was dried and weighed once in the laboratory. A stand therefore
yields exactly one ingrowth number, and it occupies exactly one line of the
file.

One row is: one surveyed spruce stand, described by the single pooled ingrowth-bag composite collected in that stand
Independent unit column: stand_id

Columns:

- stand_id: the code of the stand, unique across the file (ST-01 through ST-24).
- canopy_state: whether the stand has a closed canopy ("intact") or is a
  wind-thrown canopy gap ("gap"). Twelve stands of each kind.
- elevation_m: elevation of the stand centre in metres above sea level. Recorded
  for context only; it is not used in the comparison.
- bags_pooled: how many ingrowth bags were merged into that stand's composite.
  It is four everywhere, so it is bookkeeping rather than a measurement.
- hyphal_ingrowth_mg: the dry mass, in milligrams, of fungal mycelium washed out
  of that composite. This is the quantity compared between canopy states.

Nothing in the file is a repeated measurement of the same stand. The bags were
merged before weighing, so the file holds 24 measurements from 24 stands, and a
two-group comparison across rows compares independent stands.
