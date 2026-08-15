# Bumblebee microcolony gyne-production dataset

data/input.csv records a caged-rearing experiment on Bombus terrestris. Twenty-eight
commercially reared, queenright colonies were each installed in a separate sealed
flight arena and fed one syrup diet for their entire colony cycle: half plain sugar
syrup, half sugar syrup dosed at 2 ppb thiamethoxam. At nest teardown every colony was
dismantled once and all new queens (gynes) were counted, giving a single lifetime
total per colony.

One row is: one bumblebee colony, with its diet arm, its starting worker force, and its single end-of-cycle gyne total
Independent unit column: colony_id

Columns

- colony_id: colony label, unique across the file; no colony is entered twice.
- arena_id: the sealed flight arena the colony occupied; one arena held one colony.
- treatment: diet arm, either control (plain syrup) or exposed (2 ppb thiamethoxam).
- founding_workers: number of workers present when the colony was installed, a baseline
  size covariate used only to check that the two arms started out comparable.
- gyne_count: total new queens counted at teardown; a whole-colony lifetime total, not a
  repeated observation.

Because each colony is measured once and contributes exactly one row, the twenty-eight
rows are twenty-eight independent units, and a row-independent two-sample test applies
directly, with no pooling of within-colony repeats.
