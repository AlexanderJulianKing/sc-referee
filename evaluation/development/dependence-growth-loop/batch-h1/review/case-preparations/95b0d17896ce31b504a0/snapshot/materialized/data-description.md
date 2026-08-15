# Mason bee nest-departure directions

One nesting female mason bee was followed at each of 23 widely separated meadow
patches during a single spring. A patch held exactly one monitored bee, and no
bee was watched at more than one patch, so the bees are the independent units of
the study and the file holds one line per bee.

For every bee an observer scored a run of departures from the nest entrance and
noted, for each departure, whether the bee circled clockwise or counterclockwise
before flying off. Those repeated within-bee departures appear in the file only
as two summary counts; the analysis reduces them to a single majority-direction
call for that bee before anything is tested, so no individual departure is ever
treated as its own observation.

One row is: one individual mason bee, summarised over all of the nest departures scored for her at her own meadow patch
Independent unit column: bee_id
One trial is: one row

Columns

- bee_id: unique label for the individual bee; each label appears on a single line
- meadow_patch: the patch where that bee nested; every patch holds exactly one bee
- forewing_length_mm: right forewing length of the bee, in millimetres
- departures_scored: how many departures were watched for that bee (always an odd number, so a majority direction always exists)
- clockwise_departures: how many of those departures were clockwise; the remainder were counterclockwise

The question is whether mason bees as a group favour one circling direction. The
count handed to the exact binomial test is the number of bees whose majority
call is clockwise, out of the number of bees, compared against an unbiased
expectation of one half.
