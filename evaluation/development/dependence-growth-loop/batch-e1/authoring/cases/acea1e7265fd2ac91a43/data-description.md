# Spring colony strength after overwintering hive wraps

Sixteen honey bee colonies kept in one research apiary were carried through
a single winter. Eight of them were fitted with a breathable overwinter
wrap in November; the other eight were left bare. At the first spring
inspection each colony was opened once and the clustered bees were weighed,
with the mass recorded in kilograms.

The file has one line of column names and sixteen data lines.

Columns:

- hive_id: the colony's permanent identifier, unique across the file
- wrap_treatment: "wrapped" or "bare", decided before the winter began
- queen_age_years: age of the colony's queen at the spring inspection
- spring_cluster_mass_kg: cluster mass at the single spring weighing

One row is: one honey bee colony, weighed a single time at the spring inspection
Independent unit column: hive_id

No colony was weighed more than once and no colony identifier is repeated,
so the sixteen rows stand for sixteen separate colonies. Colonies were
never split, merged, or subsampled, and no measurement in the file is
nested inside another one.
