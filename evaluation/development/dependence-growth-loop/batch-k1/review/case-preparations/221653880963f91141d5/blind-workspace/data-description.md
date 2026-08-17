# What is in data/input.csv

Twenty-four honey bee colonies kept in a single research apiary were prepared
for winter with one of two entrance-reducer designs, notched or open, assigned
by coin toss with twelve colonies to each design. Every colony was opened once,
at the spring inspection, and given a single survival call. Nothing else was
recorded after the October assessment, so the file has one line per colony and
no colony appears twice.

One row is: one honey bee colony, carrying its assigned entrance-reducer design, its October condition, and the single survived-or-died call made at the spring inspection
Independent unit column: colony_id
One trial is: one row

Columns:

- colony_id: the painted apiary tag of the colony; each tag is used on exactly one line
- entrance_design: notched or open, the winter entrance reducer fitted in October
- autumn_bee_frames: bee-covered frames counted at the October assessment
- varroa_per_100_bees: mites per 100 bees from the October alcohol wash
- overwinter_outcome: survived or died, scored once at the spring inspection

The colonies were housed on separate stands and managed independently, and the
outcome is a terminal one-time score, so each line is one independent unit with
no repeated measurement behind it.
