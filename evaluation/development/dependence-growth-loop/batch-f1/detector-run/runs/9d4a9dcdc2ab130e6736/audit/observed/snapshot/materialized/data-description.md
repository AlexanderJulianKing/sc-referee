# What is in data/input.csv

Serra Alta olive orchard, deficit-irrigation trial. Twelve mature 'Arbequina'
trees of similar trunk girth were assigned to one of two irrigation regimes for
the whole dry season: full replacement of crop evapotranspiration, or a deficit
schedule at roughly 35 percent of that amount. Six trees received each regime.

In the third week of the stress period a single field crew walked the orchard
once, mid-morning, and measured eight sunlit leaves on every tree with a
steady-state porometer: four leaves from the east side of the canopy and four
from the west side. Each leaf was measured a single time and then tagged, so no
leaf appears twice, but every tree contributes eight readings to the file.

Columns:

- leaf_id: unique tag written on the measured leaf
- tree_id: orchard label of the tree that carried the leaf
- irrigation: irrigation regime applied to that tree, full or deficit
- canopy_aspect: side of the canopy the leaf was picked from, east or west
- gsw_mmol_m2_s: stomatal conductance of the leaf in mmol m^-2 s^-1, as read
  off the porometer (whole numbers, the resolution of the instrument display)

The file has 96 measurement lines, 8 for each of the 12 trees. Irrigation is a
property of the tree, not of the leaf: all eight leaves of a tree carry the same
regime label, and leaves from the same tree share that tree's soil water status,
rooting depth, canopy architecture and time of measurement.

One row is: one sunlit leaf measured once with a steady-state porometer on one olive tree
Independent unit column: tree_id
