# What data/input.csv contains

Each line of the table is one fallen log (a single piece of coarse woody
debris) that a two-person crew located, measured, and inspected a single time
during one summer survey of a temperate mixed forest. Twenty logs were
surveyed: ten in old-growth stands and ten in second-growth stands. Every log
came from its own survey site, the sites were chosen at least 500 m apart, and
no site contributed more than one log, so the logs do not share a plot, a stand
patch, or a visit with one another, and none of them was measured twice.

Columns:

- log_id: the label of the log, unique in the file (OG-xx for logs in
  old-growth stands, SG-xx for logs in second-growth stands).
- stand_type: which kind of stand the log came from, old_growth or
  second_growth.
- log_diameter_cm: the diameter of the log at its midpoint in centimetres,
  taken once with a diameter tape.
- fruiting_bodies_present: 1 if fruiting bodies of the target polypore were
  seen anywhere on the log during that inspection, 0 if none were seen.

Nothing in the file is a repeat visit, a subsample, or a second reading of a
log listed earlier; the twenty lines are twenty separate logs.

One row is: one fallen log, from its own survey site, inspected exactly once
Independent unit column: log_id
One trial is: one row
