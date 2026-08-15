# What is in data/input.csv

Twenty-four abandoned slate and gravel quarry ponds across one upland survey
region were screened for great crested newt environmental DNA during a single
spring campaign. Each pond was visited exactly once and yielded exactly one
pooled water sample, so a pond never appears on more than one line of the file.
Half of the ponds had been regraded years earlier to give a gently shelving
littoral margin; the other half kept their original steep-sided profile.

Columns:

- pond_id: the unique code for the quarry pond, for example QP-07. No code is
  repeated anywhere in the file.
- shelf_status: "restored" if the pond has a regraded gently shelving littoral
  margin, "unrestored" if it retains its original steep-sided profile.
- pond_area_m2: open-water surface area of the pond in square metres.
- mean_depth_cm: mean water depth in centimetres, averaged over a five-point
  transect walked during the same single visit.
- edna_result: "detected" or "not_detected", the great crested newt eDNA result
  for that pond's one pooled water sample.

One row is: one abandoned quarry pond surveyed a single time, with one pooled water sample screened for great crested newt eDNA
Independent unit column: pond_id
One trial is: one row

Every pond is its own independent unit. There are no repeat visits, no split or
replicate samples written out as extra lines, and no grouping of ponds inside
larger clusters recorded in this file, so the rows can be treated as separate
observations of separate ponds.
