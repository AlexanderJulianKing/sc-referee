# Wrack Bay coastal aquifer chloride monitoring

Wrack Bay is a barrier-island lagoon whose shallow freshwater lens is watched
for saltwater intrusion. Thirty permanent monitoring wells are screened in the
surficial aquifer, and each well belongs to one of three shoreline zones: the
dune ridge farthest from open water, the back-barrier flats behind it, and the
tidal flat nearest the inlet. Every well was visited four times during a single
field season. On each visit the well was purged and one grab sample was pumped
from the screen and sent to the laboratory for chloride analysis. The file
therefore holds 120 sample rows: four rows for each of the thirty wells.

Columns:

- well_id: identifier of the monitoring well the sample was pumped from. The
  same well identifier appears once for each of its four visits, so identifiers
  repeat down the file.
- coastal_zone: the shoreline zone the well sits in (dune_ridge, back_barrier,
  tidal_flat). This is a fixed property of the well, so it is identical across
  all four rows belonging to that well.
- visit: which of the four scheduled sampling visits produced this row,
  numbered 1 through 4.
- depth_m: screened depth of the well below ground surface, in metres. Another
  fixed well property, repeated on all four of that well's rows.
- chloride_mg_l: chloride concentration measured in that visit's grab sample,
  in milligrams per litre. The regulatory action limit used by the programme is
  250 mg/L.

One row is: one grab sample pumped from one monitoring well on one scheduled visit
Independent unit column: well_id
