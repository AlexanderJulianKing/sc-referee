# Y-maze thermal choice assay in juvenile cave salamanders

Five juvenile cave salamanders were collected from a single spring outflow, held
in a common tank on the same feeding schedule, and tested in a two-armed Y-maze
in which one arm was warmed to about 18 degrees C while the other was held near
11 degrees C. Each animal was released into the start box four times, once per
day on four consecutive days, giving twenty scored releases in total. For every
release an observer recorded which arm the animal entered first and how many
seconds passed between release and that first entry. The warm and cool arms were
swapped between days so that a fixed side preference could not by itself produce
the pattern of choices.

The file data/input.csv has one line per scored release. The columns are:

- trial_uid: label for the scored release, T01 through T20
- salamander_id: the animal that was released, SAL-01 through SAL-05
- trial_day: which of the four testing days the release belongs to, 1 through 4
- arm_chosen: the arm entered first, either warm or cool
- latency_s: whole seconds from release to the first arm entry

Because every animal appears on four separate lines, the same five salamanders
account for all twenty lines in the file.

One row is: one Y-maze release of one salamander on one day, recording the arm it entered first and the latency to that entry
Independent unit column: salamander_id
One trial is: one row
