# What data/input.csv holds

A small greenhouse trial on potted sunflowers. Six pots were grown in a single
run: three pots received a biochar soil amendment and three pots were left
unamended. Near midday, a porometer was clamped on two leaves of every plant
(one lower-canopy leaf and one upper-canopy leaf) and the steady-state stomatal
conductance of each leaf was written down as its own line in the file.

One row is: one porometer reading taken on a single leaf of one potted sunflower
Independent unit column: plant_id

Columns:

- plant_id: label of the pot and its plant, PL-01 through PL-06. Each label
  appears twice because two leaves of that plant were measured.
- amendment: soil treatment of the pot, either control or biochar. It is fixed
  for a plant, so both rows of a plant carry the same value.
- leaf_position: which leaf of the plant supplied the reading, lower or upper.
- conductance_mmol_m2_s: stomatal conductance of that leaf in mmol per square
  metre per second, recorded to one decimal place.

The twelve rows therefore come from six plants, three per amendment group, with
two leaf readings per plant.
