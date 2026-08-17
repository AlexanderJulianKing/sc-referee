# What is in data/input.csv

The file holds the field records from a leafcutter ant foraging study. Twenty-six
colonies of *Atta cephalotes* were excavated, each from its own forest plot, and
kept in separate laboratory nests. Every colony was then run through a two-choice
foraging arena on a single occasion: two leaf trays of equal starting mass were
offered side by side for six hours, one tray sprayed with a dilute urea solution
and one left untreated. After the window closed, the leaf mass each colony had
carried away from each tray was weighed.

Because every colony went through the arena once and appears in the file once,
the file contains no repeated visits, no repeated sessions, and no split
sub-samples of a single nest.

## Columns

- `colony_id` -- the code for the colony, unique across the file.
- `nest_origin_plot` -- the forest plot the colony was dug from; one plot per
  colony, so plot codes are unique too.
- `forager_count` -- how many workers were active in the arena for that colony.
- `cut_mass_urea_mg` -- milligrams of leaf the colony removed from the
  urea-supplemented tray.
- `cut_mass_plain_mg` -- milligrams of leaf the colony removed from the
  untreated tray.

The two mass columns are the two halves of a single choice made by one colony;
together they say which tray that colony favoured, which is the one outcome the
colony contributes to the analysis.

One row is: one leafcutter ant colony and its single two-choice foraging session, with the leaf mass it cut from the urea-supplemented tray and from the untreated tray
Independent unit column: colony_id
One trial is: one row
