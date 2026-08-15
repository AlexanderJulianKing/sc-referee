# Constructed wetland mesocosm outflow: dissolved zinc

Twelve bench-scale constructed treatment wetlands (called mesocosms) were built
in a greenhouse to test whether a biochar-amended substrate lowers the dissolved
zinc carried in water leaving a wetland cell. Six mesocosms were packed with the
biochar-amended substrate and six with the plain gravel control substrate. All
twelve were fed the same synthetic zinc-bearing influent from a shared
reservoir, and the outflow of every mesocosm was sampled on the same four dates
(weeks 2, 4, 6 and 8 of the run), so each mesocosm contributes four separate
water samples to the file.

One row is: one outflow water sample taken from one mesocosm on one sampling week
Independent unit column: mesocosm_id

Columns

- mesocosm_id: label of the physical mesocosm the water sample came from, MC-01
  through MC-12. Each label appears on four rows, one per sampling week.
- substrate: which substrate that mesocosm was packed with, either
  biochar_amended or gravel_control. It was fixed when the mesocosm was built
  and never changed during the run.
- sampling_week: the week of the run on which the outflow sample was collected
  (2, 4, 6 or 8).
- zinc_mg_per_l: dissolved zinc concentration measured in that outflow sample,
  in milligrams per litre.

The file holds 48 rows, which is 12 mesocosms times 4 sampling weeks. The
substrate treatment was assigned to whole mesocosms, never to individual water
samples, and samples drawn from the same mesocosm share its packing, its
planting and its hydraulic history.
