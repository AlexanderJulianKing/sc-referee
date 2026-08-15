# Pilot fermenter harvest titers

A pilot-scale ethanol project compared a wild-type Zymomonas mobilis strain with an
engineered derivative. Twelve 20 L fermenters were prepared, six for each strain, and
each fermenter was inoculated from its own seed lot and taken through a single run to
harvest. When a run ended, one harvest sample was drawn from that vessel and its
ethanol concentration was measured; that single number is the vessel's entry in the
table. No vessel was reused, split between strains, or sampled a second time, so the
twelve rows stand for twelve separate experimental runs.

Columns in data/input.csv:

- vessel_id: label of the pilot fermenter, V01 through V12, each appearing once.
- strain_arm: the strain inoculated into that vessel, either wildtype or engineered
  (six vessels each).
- inoculum_lot: identifier of the seed culture lot used for that vessel; every vessel
  had a lot of its own.
- final_titer_g_per_l: ethanol concentration in the harvest sample, in grams per litre.

One row is: one pilot fermenter, described by the single ethanol titer measured in its harvest sample
Independent unit column: vessel_id
