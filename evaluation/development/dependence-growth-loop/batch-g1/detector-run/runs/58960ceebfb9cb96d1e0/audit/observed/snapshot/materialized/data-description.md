# data/input.csv - midday gas-exchange sessions in a deficit-irrigation crossover

Sixteen two-year-old potted olive saplings (cv. Arbequina) were grown in a ventilated
screenhouse and put through a two-phase irrigation crossover during the summer of
2025. Each sapling spent one phase on a deficit schedule (about 35% of estimated crop
evapotranspiration) and one phase on a full schedule (100% of estimated crop
evapotranspiration). Half of the saplings started on the deficit schedule and half
started on the full schedule, so the order of the two schedules is counterbalanced
across saplings.

Midday leaf gas exchange was measured on four dates spaced two weeks apart, two dates
inside each irrigation phase, always between 12:00 and 13:30 local time on the
youngest fully expanded sun-exposed leaf of the sapling. The file is stored in long
format: the four sessions of a sapling appear as four separate rows, so every sapling
contributes four rows to the file.

Columns:

- sapling_id: label of the potted sapling that was measured (OLV-01 to OLV-16). The
  same label appears on all four session rows of that sapling.
- orchard_block: screenhouse bench the pot stood on (B1 to B4), four pots per bench.
- session_index: 1 to 4, the ordinal position of the measurement date.
- session_date: calendar date of the measurement session.
- irrigation_regime: the schedule the sapling was on during that session, either
  "deficit" or "full".
- leaf_temp_c: leaf temperature in the cuvette at the time of the reading, in degrees
  Celsius.
- stomatal_conductance_mmol_m2_s: midday stomatal conductance to water vapour, in
  mmol m^-2 s^-1.

Each sapling is its own pot with its own dripper and is the experimental unit of the
study. The four rows carrying the same sapling label are repeated measurements of one
plant, not measurements of four different plants.

One row is: one midday gas-exchange session on one potted olive sapling on one date
Independent unit column: sapling_id
