# Sourdough leavening trial: timed rise readings

The file `data/input.csv` comes from a small bakery-lab trial comparing two
flours. Twelve starter jars were built and kept together in one proofing
cabinet: six jars were fed rye flour and six were fed spelt flour, so the flour
treatment belongs to the jar, not to any single measurement. After feeding, a
technician returned to every jar four times, at 6, 12, 18 and 24 hours, and each
time recorded the height of the risen gas column and the pH of the starter.
Because of that schedule, each jar shows up in the file four times, once per
visit, and those four numbers come from the same batch of dough.

Columns:

- `reading_id`: label for one measurement event (48 of them, all distinct).
- `jar_id`: which starter jar was measured; twelve jars in total.
- `flour_type`: the flour fed to that jar, either `rye` or `spelt`.
- `incubation_h`: hours elapsed since feeding when the reading was taken.
- `starter_ph`: pH of the starter at that reading.
- `rise_mm`: height of the risen dough column, in millimetres, at that reading.

One row is: one timed measurement of rise height and pH taken from a single starter jar at a single incubation time
Independent unit column: jar_id
