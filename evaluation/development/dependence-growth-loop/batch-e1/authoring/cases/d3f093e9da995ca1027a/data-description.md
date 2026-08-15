# What is in data/input.csv

The file records closed-chamber respirometry of mayfly (Baetis) nymphs netted
from a single alpine catchment. Three nymphs came from the lowland reach of the
catchment and three from the highland reach, six animals in total. Every animal
was weighed once and then placed in the respirometer on two consecutive
mornings, so each animal contributes two measurement records to the file. The
file has 12 records under a single header row.

One row is: one closed-chamber respirometry run on a single mayfly nymph
Independent unit column: nymph_id

Columns:

- run_id: label of the respirometry run, unique across the file.
- nymph_id: field tag of the animal measured in that run. Each tag appears
  twice, once for the first morning and once for the second morning.
- elevation_band: reach the animal was netted from, lowland or highland. It is
  a property of the animal, so it is identical for both runs of a given tag.
- run_order: 1 for the first morning, 2 for the second morning.
- mass_mg: wet mass of the animal in milligrams, measured once before the first
  run and repeated in both of its records.
- metabolic_rate_ul_o2_per_h_mg: oxygen uptake during the run in microlitres
  per hour per milligram of wet mass.

The two runs of one animal are repeat readings of that animal, not readings of
two different animals.
