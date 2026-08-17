# Archerfish two-choice shooting assay

Five captive archerfish, each carrying a numbered tag (AR-11, AR-14, AR-22,
AR-27, AR-31), were tested in a covered freshwater tank. On four separate days
each fish took part in one testing session, and each session produced one
shooting trial, so every fish contributes four lines to the file and the file
holds twenty lines of data in total.

In a trial the fish saw two paper targets held above the water surface at the
same height and the same distance apart: the rewarded shape (a disc, or in the
later sessions a cross) and an unrewarded bar. The fish knocked one target down
with a jet of water, and only the target hit by its first shot was scored. A hit
on the rewarded shape earned a food pellet.

Columns in data/input.csv:

- trial_uid: label of the individual shooting trial
- fish_tag: tag of the fish that performed the trial
- session: which of that fish's four sessions the trial came from (1 to 4)
- standoff_cm: horizontal distance from the fish's launch spot to the targets
- water_temp_c: tank water temperature during the trial, in degrees Celsius
- target_pair: which pair of shapes was shown (disc_vs_bar or cross_vs_bar)
- latency_s: seconds between showing the targets and the fish's first shot
- chose_target: 1 if the first shot struck the rewarded shape, 0 if it struck
  the unrewarded bar

One row is: one two-choice shooting trial performed by one tagged archerfish
Independent unit column: fish_tag
One trial is: one row
