# What is in data/input.csv

Six adult whip spiders (Phrynus laevifrons) were released one at a time into a
darkened T-junction arena and allowed to walk into either the left or the right
arm. Every animal was run six times on the same evening, so the file holds
thirty-six runs in total: six consecutive runs for each of the six individuals.
The arena was wiped down between runs and the two arms were swapped in position
halfway through the session.

Columns:

- animal_id: the code of the individual whip spider (AMB-01 through AMB-06).
- trial_index: which of that animal's six runs this row describes (1 to 6).
- arm_chosen: the arm the animal walked into, either "left" or "right".
- latency_s: seconds from release to crossing the choice point.

One row is: one T-junction run by one whip spider
One trial is: one row
Independent unit column: animal_id
