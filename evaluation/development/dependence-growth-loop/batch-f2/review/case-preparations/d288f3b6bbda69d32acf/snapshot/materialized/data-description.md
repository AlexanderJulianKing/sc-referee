# What is in data/input.csv

Twelve Avicennia marina (grey mangrove) seedlings were raised in a glasshouse
for eight weeks: six pots were watered with a 15 ppt saline solution and six
with a 35 ppt solution. At the end of the growth period a portable infrared gas
analyser was clamped onto eight fully expanded leaves of every seedling, one
leaf at a time, and the steady-state net CO2 assimilation rate was logged for
each leaf. The file therefore holds eight readings for each of the twelve
seedlings, 96 readings in all.

Columns:

- measurement_id: label for a single leaf reading (M001 through M096).
- seedling_id: the potted seedling that the clamped leaf grew on (MG01 through
  MG12). Readings sharing a seedling_id come from the same plant.
- salinity_regime: the watering solution the pot received, either
  ambient_15ppt or elevated_35ppt. A whole seedling sits in one regime, so all
  eight readings from a seedling carry the same label.
- leaf_rank: which leaf on that seedling was clamped, counted from the shoot
  apex downwards (1 to 8).
- anet_umol_m2_s: net CO2 assimilation rate for that leaf, in umol CO2 per
  square metre of leaf area per second.

One row is: one gas-exchange reading taken from one leaf of one mangrove seedling
Independent unit column: seedling_id

The salinity treatment was applied to whole pots rather than to individual
leaves, so the treatment label varies between seedlings and never within one.
