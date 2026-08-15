# Y-maze colour-choice assay on marked bumblebee foragers

Six individually paint-marked bumblebee foragers from one commercial colony were
tested in a Y-maze that offered a UV-bright artificial corolla in one arm and a
visually matched UV-dull corolla in the other arm. The arm holding the UV-bright
corolla was swapped between releases so that a bee could not solve the task by
position alone. For every release we recorded which corolla received the bee's
first landing and how long that landing took. Foragers were run in up to four
test blocks, so most bees appear in the file several times; the number of
releases per bee differs because some individuals stopped foraging early.

One row is: one Y-maze release in which a single marked forager made a first landing on either the UV-bright or the UV-dull artificial corolla
Independent unit column: forager_id
One trial is: one row

Column guide:

- trial_uid: unique label for the release, numbered in the order the releases were run
- forager_id: paint mark of the bee that was released
- test_block: which of the four test blocks the release belongs to (B1 to B4)
- arena_arm_uv_bright: maze arm, L or R, that held the UV-bright corolla for that release
- first_visit_choice: corolla that received the first landing, either uv_bright or uv_dull
- latency_s: seconds from release to that first landing

The file contains 20 releases contributed by 6 bees, with between two and four
releases per bee.
