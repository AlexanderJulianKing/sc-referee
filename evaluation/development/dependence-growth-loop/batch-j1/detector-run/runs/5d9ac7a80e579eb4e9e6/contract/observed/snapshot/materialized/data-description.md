# What is in data/input.csv

The file records an alpine warming-chamber foraging assay on ten bumblebee (*Bombus sylvicola*) colonies collected from three cirque sites. Every colony was tested twice over: two sessions in a chamber held near 19 C (ambient) and two sessions in a chamber held near 26 C (warmed), with two 30-minute observation trials inside each session. Half of the colonies ran the ambient block first and half ran the warmed block first. During each trial an observer counted foragers returning to the nest entrance and converted the count to a rate per hour.

One row is: one 30-minute foraging trial for one colony during one chamber session
Independent unit column: colony_id

## Columns

- colony_id: label of the colony that was observed (C01 to C10). Colonies were collected and housed separately, so different colonies are independent of one another.
- site: alpine site the colony came from (Wheeler Cirque, Trapper Basin, or Sundog Pass).
- block_order: AW if the colony completed its ambient block first, WA if it completed its warmed block first.
- condition: chamber setting during the trial, either ambient or warmed.
- session: chronological session number for that colony, 1 to 4. Sessions 1 and 2 are the colony's first block, sessions 3 and 4 its second block.
- trial: which of the two observation trials within the session, 1 or 2.
- chamber_temp_c: air temperature inside the chamber during the trial, in degrees Celsius.
- sorties_per_hour: returning foragers per hour counted at the nest entrance during the trial. This is the measured outcome.

## How the rows relate to each other

Each colony contributes eight rows (2 conditions x 2 sessions x 2 trials), so rows within a colony are repeated measurements of the same nest and are correlated: they describe how precisely that colony's foraging rate was measured, not how many colonies responded to warming. The four trials of a colony within a condition should therefore be averaged into a single value per colony per condition, leaving ten independent paired observations, one per colony, for any comparison of the two chamber settings. There are 80 rows in total.
