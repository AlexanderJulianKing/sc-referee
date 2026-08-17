# data/input.csv in plain language

This file records a 60-day grow-out trial at a marine hatchery. Twenty-four
juvenile Atlantic cod were tagged, weighed, and moved into twenty-four separate
flow-through chambers, one fish per chamber. Half the chambers were fed the
standard baseline pellet and half were fed the same pellet with an algal-oil
supplement, and that assignment was fixed for the whole trial. Each fish was
weighed once, at day 60, and that single weight is the only outcome recorded for
it. A fish is said to have graded out if it reached the hatchery's 12.0 g
transfer target.

One row is: one juvenile Atlantic cod that was reared alone in its own flow-through chamber for the whole 60-day trial and weighed once at day 60
Independent unit column: chamber_id
One trial is: one row

Columns
- chamber_id: label of the flow-through chamber, for example CH07. Because
  exactly one fish lived in each chamber and no chamber was reused, this label
  appears on exactly one row and so identifies the fish.
- diet: which feed the fish received for the whole trial, either baseline or
  algal_oil.
- day60_mass_g: the fish's wet mass in grams at the single day-60 weighing.

Nothing in the file is a repeated measurement: no fish was weighed more than
once, no chamber held more than one fish, and no chamber contributes more than
one row. The twenty-four rows are therefore twenty-four independent units, which
is what lets a row-independent test be applied directly to them.
