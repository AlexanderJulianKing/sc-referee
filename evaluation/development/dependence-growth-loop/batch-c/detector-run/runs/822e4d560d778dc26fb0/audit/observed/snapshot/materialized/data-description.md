# What data/input.csv contains

A wildfire burned a contiguous block of montane pine forest on Kelsang Ridge.
For post-fire management the burned block was split into 26 compartments of
roughly equal size, separated from one another by ridgelines and drainages.
Thirteen compartments, drawn by lot before any survey work began, were treated
with aerial seeding of locally collected pine seed; the other thirteen were
left to regenerate on their own.

Three growing seasons later, each compartment was flown once with a drone and
the whole compartment was censused for surviving pine stems, which yields a
single regeneration density for that compartment. Nothing inside a compartment
was measured twice and no compartment was flown twice, so each compartment
shows up in the file exactly once and the file has 26 data rows.

One row is: one burn compartment, censused once by drone three growing seasons after the fire
Independent unit column: compartment_id

Columns

- compartment_id: label of the burn compartment, unique across the file
- aerial_seeding: "yes" if the compartment was aerially seeded, "no" if it was left to natural recovery
- elevation_m: mean elevation of the compartment, in metres above sea level
- pine_stems_per_ha: surviving pine stems per hectare from the drone census

The seeding treatment was applied to whole compartments, and the outcome is
measured at the same whole-compartment scale, so a comparison between the two
treatment groups has 13 independent values on each side.
