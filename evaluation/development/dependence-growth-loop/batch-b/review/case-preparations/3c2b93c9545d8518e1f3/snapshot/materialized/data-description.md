Kessel Glacier ablation-stake survey (data/input.csv)

Over one week in late July, a two-person field team drilled eight aluminium
stakes into the bare-ice zone of Kessel Glacier: four on a north-facing bench
and four on the south-facing flank across the valley. Every morning for six
mornings the team measured how far the ice surface had dropped below the collar
of each stake since the previous morning, and logged the shaded air temperature
at the stake at the moment of the reading.

One row is: one morning melt reading at one ablation stake, that is, the surface lowering measured at that stake over the preceding 24 hours
Independent unit column: stake_id

Columns
- stake_id: label of the ablation stake the reading came from. The same eight
  stakes are revisited, so each label appears on all six survey mornings.
- slope_aspect: whether the stake sits on the north-facing or the south-facing
  side of the valley. Fixed for a given stake.
- survey_day: survey morning, numbered 1 to 6 from the start of the week.
- ablation_mm: surface lowering in millimetres over the preceding 24 hours.
- air_temp_c: shaded air temperature in degrees Celsius at the stake when the
  reading was taken.

The stakes were placed once and left in the ice for the whole week; nothing was
re-randomised between mornings.
