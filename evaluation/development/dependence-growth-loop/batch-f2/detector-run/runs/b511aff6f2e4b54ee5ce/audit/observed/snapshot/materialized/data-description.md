# What is in data/input.csv

The file holds stomatal conductance readings from a screenhouse misting
trial on potted coffee shrubs. Five shrubs were used. On each shrub, four
leaves were tagged. Every tagged leaf was clamped in a porometer once just
before a 90-second canopy misting pulse and once again about 90 seconds
after the pulse ended, so each tagged leaf contributes one before value and
one after value. All five shrubs were misted in the same session with the
same nozzle setting; the four leaves on a shrub share that shrub's pot,
watering history, canopy position and mist exposure.

One row is: one tagged coffee shrub leaf, with its conductance read once before and once after the misting pulse
Independent unit column: shrub_id
One trial is: one row

Columns:

- shrub_id: label of the potted shrub the tagged leaf grew on. Five labels,
  S-01 through S-05, each appearing on four rows.
- leaf_tag: label of the tagged leaf within its own shrub (L1 to L4). The
  same four tags are reused on every shrub, so leaf_tag only identifies a
  leaf once you also know shrub_id.
- pre_mist_gs: stomatal conductance measured just before the misting pulse,
  in mmol per square metre per second, rounded to whole units.
- post_mist_gs: stomatal conductance measured about 90 seconds after the
  pulse, same units and rounding.

No values are missing and no leaf was measured twice at the same time point.
