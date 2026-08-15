# What is in data/input.csv

Twenty-four juvenile mangrove mud crabs were hand-collected from the tidal
creeks behind a mangrove fringe, held individually in aerated bins, and then
released once at the base of a two-armed water flume. One arm carried water
carrying the outgoing-tide chemical cue; the other arm carried filtered
seawater as a control. The arm the crab entered first was recorded, the crab
was removed, and it was never tested again. Every crab therefore appears on
exactly one line of the file, and no line summarises more than one crab.

One row is: one juvenile mud crab that completed a single Y-maze arm-choice trial
Independent unit column: crab_id
One trial is: one row

Columns:

- crab_id: the code painted on the crab's carapace; each code appears on
  exactly one row, so the codes are all distinct.
- sex: F or M, scored from the shape of the abdominal flap before testing.
- carapace_width_mm: carapace width in millimetres, measured with calipers
  on the day of the trial.
- arm_choice: which arm the crab entered first, written as "tidal" for the
  arm with the tide cue and "control" for the filtered-seawater arm.

Because each crab supplies one binary choice and nothing else, the rows can
be counted as independent trials without any grouping or averaging step.
