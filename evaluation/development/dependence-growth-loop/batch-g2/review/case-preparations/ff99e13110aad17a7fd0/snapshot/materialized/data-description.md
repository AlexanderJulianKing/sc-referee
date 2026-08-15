# Cold-brew steeping trial

Twelve laboratory cold-brew vessels were prepared in a temperature-controlled
cabinet. Each vessel was filled with coffee ground at a single setting, either
coarse or fine, and then sampled four times as the brew steeped: at 6, 12, 18
and 24 hours. At every sampling a small aliquot was drawn and its total
dissolved solids (TDS) measured with a refractometer, and the water temperature
of the vessel was noted. Six vessels used the coarse setting and six used the
fine setting, giving 48 measurement records in all.

Columns in data/input.csv:

- vessel_id: label of the steeping vessel, V01 through V12. Each vessel appears
  in four rows, one per draw time.
- grind: the grind setting loaded into that vessel, "coarse" or "fine". The
  setting is a property of the vessel, so it is the same in all four of a
  vessel's rows.
- steep_hours: hours of steeping elapsed when the aliquot was drawn (6, 12, 18
  or 24).
- water_temp_c: water temperature of the vessel in degrees Celsius.
- tds_percent: total dissolved solids of the drawn aliquot, percent by mass.

One row is: one aliquot drawn from one steeping vessel at one draw time
Independent unit column: vessel_id
