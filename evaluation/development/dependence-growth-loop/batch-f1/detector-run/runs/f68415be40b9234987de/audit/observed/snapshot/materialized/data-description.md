# What data/input.csv holds

A peatland methane survey. Twenty-four static-chamber gas-flux collars were
installed across twenty-four separate raised-bog basins in the same region,
one collar per basin, with basins chosen far enough apart that their water
tables are hydrologically disconnected. Twelve of the basins still drain
through nineteenth-century ditches (management = drained); the other twelve
were ditch-blocked and rewetted at least eight years before the survey
(management = restored).

Each collar was visited once, on a single dry midsummer morning, and one
closed static chamber was seated on it for one thirty-minute closure. The
methane efflux computed from that one closure is the only response value the
collar ever contributes. Nothing was measured twice on a collar, and no value
in the file is an average of several readings, so the twenty-four response
numbers are twenty-four separate observations rather than repeats.

Columns:
- collar_id: unique label of the gas-flux collar, which also identifies the
  basin it sits in (each label appears on exactly one row)
- management: drained or restored
- peat_depth_cm: peat thickness probed beside the collar, recorded for site
  context only and not used in the comparison
- ch4_flux_mg_m2_h: methane efflux from that collar's single chamber closure,
  in milligrams of CH4 per square metre per hour

One row is: one gas-flux collar in its own peat basin, together with the single methane efflux measured during that collar's one and only chamber closure
Independent unit column: collar_id
