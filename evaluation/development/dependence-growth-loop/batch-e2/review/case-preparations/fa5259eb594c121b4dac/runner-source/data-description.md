# Y-bridge arm-choice assay (data/input.csv)

Five queenright Lasius niger colonies, each collected from a separate roadside
verge and housed in its own nest box, were tested four times apiece on a Y-shaped
foam bridge. In every test one arm of the bridge carried a freshly applied
trail-pheromone extract and the other arm was left plain; the side carrying the
extract was alternated between successive tests of a colony. A single
paint-marked forager was released at the base of the bridge, the arm it committed
to was recorded, and the observer logged how long the forager took to cross the
choice line and how many nestmates were on the bridge at that moment.

One row is: one Y-bridge test of a single forager from one colony, giving the arm it chose, its commitment latency, and the bridge traffic at the moment of choice
Independent unit column: colony_id
One trial is: one row

Columns:

- colony_id: the source colony (COL-01 through COL-05); each colony contributed
  four tests, so the same colony appears on four rows
- trial_no: position of the test within that colony's own sequence, 1 to 4
- arm_chosen: "marked" if the forager took the pheromone-treated arm, "plain" if
  it took the untreated arm
- latency_s: seconds from release until the forager crossed the choice line,
  recorded to one decimal place
- foragers_on_bridge: count of other foragers on the bridge at the moment the
  choice was made

There are 20 rows in total: 5 colonies x 4 tests. Colonies differ noticeably from
one another in how strongly they follow the extract, and tests from the same
colony were run with the same nest, the same forager pool, and the same batch of
pheromone extract.
