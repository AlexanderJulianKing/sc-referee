# Denitrifying bioreactor carbon-source trial

Ten bench-scale denitrifying bioreactors were run for six weeks on synthetic
nitrate-laden wastewater under matched flow and temperature settings. Each
vessel was assigned a single external carbon source for the whole run: five
vessels were dosed with methanol and five with glycerol. The nitrate removal
rate of every vessel was measured on six sampling days (run days 7, 14, 21,
28, 35 and 42), so the file holds 60 measurement records drawn from 10
vessels.

Columns:

- reactor_id: label of the bench-scale reactor vessel (R01 through R10).
- carbon_source: the external carbon source dosed to that vessel for the
  entire run, either methanol or glycerol.
- run_day: the day of the run on which the sample was drawn.
- nitrate_removal_mg_n_per_l_per_h: the measured nitrate removal rate, in
  milligrams of nitrogen per litre per hour.

One row is: one nitrate removal measurement taken from one bioreactor vessel on one sampling day
Independent unit column: reactor_id
