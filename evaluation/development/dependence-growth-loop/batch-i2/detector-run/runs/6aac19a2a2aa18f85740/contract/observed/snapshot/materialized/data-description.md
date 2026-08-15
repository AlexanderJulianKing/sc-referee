# What data/input.csv contains

A single midsummer field campaign visited twelve upland peat bogs, each sitting in its own
catchment, and took one closed-chamber methane flux reading at each bog. Six of the bogs still
hold an intact water table; the other six were drained by historic ditching. No bog was visited
twice, and no two rows describe the same bog, so the twelve rows are twelve separate sites.

One row is: one surveyed peat bog together with its single midsummer methane flux reading
Independent unit column: bog_id

Columns
- bog_id: site code of the bog; each code appears on exactly one row
- catchment: name of the catchment the bog sits in; each catchment holds exactly one of the bogs
- hydrology: management state of the bog, either intact or drained
- peat_depth_cm: depth of the peat column at the chamber position, in centimetres
- ch4_flux_mg_m2_h: methane flux measured at the chamber, in milligrams per square metre per hour

Because measurement, bog, and row are one and the same thing here, the readings can be compared
between the two hydrology classes without any grouping or repeated-measures structure to account
for. Peat depth is recorded for context only and is not used by the analysis.
