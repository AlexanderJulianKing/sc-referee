# Berry skin anthocyanin across Syrah vineyard blocks

This file comes from a harvest-season survey of commercial Syrah plantings in a
warm inland growing region. Growers there train their vines either on vertical
shoot positioning, which holds the canopy in a narrow upright wall and leaves
fruit relatively exposed, or on a sprawl system, which lets shoots fall outward
and shades the fruit zone more heavily. The survey asked a simple question:
does the trellis system go along with a difference in anthocyanin, the pigment
that gives red wine its colour, in the berry skins at harvest?

Twenty-four blocks were surveyed. Each block sits at a different estate, is
owned and farmed separately, and is trained entirely on one system, so the
blocks do not share management, irrigation, or picking decisions with one
another. Fieldwork in each block was done once, on the morning that block was
picked. A crew walked a zigzag transect and collected 100 berries spread across
the block; those berries were pooled into a single composite before the skins
were ever extracted, so the laboratory produced one anthocyanin number per
block rather than many. The canopy density figure was likewise averaged in the
field across a fixed set of point-quadrat insertions and written down once.

One row is: one independently owned and managed Syrah vineyard block, summarized by the single 100-berry composite sample collected in that block on its harvest day
Independent unit column: block_id

## Columns

- `block_id`: the survey code for the vineyard block, for example BLK-07. Each
  code appears on exactly one row; there are as many rows as blocks.
- `trellis_system`: how the block is trained, either `vsp` (vertical shoot
  positioning) or `sprawl`. Twelve blocks of each. This is a property of the
  block, not something that varies within it.
- `vine_age_years`: age of the planting in whole years at the time of the
  survey.
- `canopy_leaf_layers`: mean number of leaf layers between the outside of the
  canopy and the fruit, from point-quadrat counts already averaged to the block
  level. Higher values mean shadier fruit.
- `anthocyanin_mg_per_g`: total anthocyanin in the pooled berry-skin composite,
  in milligrams per gram of skin.

## How to read the file for analysis

Because the pooling and averaging happened in the field, the file is already at
the level at which the science operates: one block, one line, one anthocyanin
value. Nothing needs to be collapsed or averaged before comparing the two
trellis groups, and no block can contribute more than one value to a group. The
vine age and canopy density columns are background context for interpreting the
comparison; they are not required to carry it out.
