# What is in data/input.csv

Every record comes from one bumblebee (Bombus terrestris) microcolony. Each
microcolony was bought as a separate unit, housed in its own rearing box on its
own food supply, and watched until its first male (drone) appeared. Nothing was
measured twice: a colony was scored on the single day its first drone emerged
and then left the study. So each colony contributes exactly one number and shows
up exactly once in the file, and colonies do not share boxes, mothers, or
batches with one another.

One row is: one bumblebee microcolony, scored a single time at the emergence of its first drone

Independent unit column: colony_id

The columns are:

- colony_id: the label of the microcolony; every label occurs exactly once in
  the file
- founding_queen_age_days: how old the founding queen was, in days, when the
  colony was set up
- initial_worker_count: how many workers were in the box at the start
- pollen_consumed_g: grams of pollen the colony ate before its first drone
  emerged
- days_to_first_drone: whole days from setup until the first drone was seen;
  this is the measured outcome

The value of 30 days used as a comparison point is the emergence day recorded
earlier for this commercial stock. It is a fixed reference number that was set
before these colonies were reared, not something computed from this file.
