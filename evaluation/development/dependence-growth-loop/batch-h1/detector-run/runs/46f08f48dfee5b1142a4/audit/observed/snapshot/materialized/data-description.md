# Bumble bee array-choice bouts

Eight queenright Bombus impatiens colonies were each connected in turn to a
flight arena holding two artificial flower arrays: one whose corolla discs are
UV-reflective and one plain white. Every colony was watched during three
separate foraging bouts on three different mornings, and an observer tallied
every landing on each array during the bout. The side of the arena holding the
UV-reflective array was swapped between bouts.

One row is: one foraging bout by one colony, with the landing tallies for both arrays
Independent unit column: colony_id
One trial is: one row

Columns:
- colony_id: label of the source colony, C01 through C08; three rows carry each label
- bout_index: 1, 2 or 3, the order of the bout for that colony
- array_side: side of the arena that held the UV-reflective array during the bout
- visits_uv: number of landings on the UV-reflective array
- visits_white: number of landings on the plain white array
- bout_minutes: length of the observation window, in minutes

The three bouts belonging to a colony draw on the same set of foragers and the
same colony-level state, so rows sharing a colony_id are related to one another
rather than free-standing observations.
