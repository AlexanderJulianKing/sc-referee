# North Ridge service reservoir chlorine survey

`data/input.csv` holds the raw water-quality readings from a spring flushing
survey of twelve municipal service reservoirs (drinking-water storage tanks) in
the North Ridge distribution zone. Each reservoir has either an epoxy interior
liner or a cement-mortar interior liner, and each one was tapped at the same
four fixed sampling ports (1.5, 3.0, 4.5 and 6.0 m below the full-tank water
line) during a single visit. Every reservoir therefore appears in four separate
rows of the file, and its identifier repeats once per port depth.

Columns:

- `tank_id`: the reservoir the sample came from, e.g. TK-102. Twelve distinct
  reservoirs appear, each in four rows.
- `liner_type`: the interior lining of that reservoir, either `epoxy` or
  `cement-mortar`. It is a fixed property of the reservoir, so it is the same in
  all four rows belonging to a reservoir.
- `port_depth_m`: depth of the sampling port below the water line, in metres.
- `free_chlorine_mgl`: free chlorine residual measured in that sample, in
  milligrams per litre.
- `water_temp_c`: water temperature at that port at the moment of sampling, in
  degrees Celsius.

One row is: a single water sample drawn from one sampling port of one reservoir, with the free chlorine residual and water temperature measured on that sample.
Independent unit column: tank_id
