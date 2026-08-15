# Kettle Fen rewetting trial - static-chamber methane flux

This file records greenhouse-gas measurements collected with closed static
chambers at the Kettle Fen peatland restoration site. Three chamber plots sit
inside the rewetted compartment and three sit in the compartment that is still
drained. Every plot carries a permanent collar set into the peat, and the same
collar was sampled on three separate survey rounds, so each plot contributes
more than one line to the file.

One row is: one static-chamber methane flux measurement taken at one chamber plot during one survey round

Independent unit column: plot_id

Columns:

- plot_id: permanent chamber plot identifier (KF-01 through KF-06); the same identifier reappears once per survey round
- treatment: hydrological management of the compartment the plot sits in, either "rewetted" or "drained"
- survey_round: sampling campaign number, 1 to 3; all six plots were visited in every round
- ch4_flux_mg_m2_h: methane flux derived from the closed-chamber concentration regression, in milligrams of CH4 per square metre per hour
- water_table_cm: water table depth relative to the peat surface in centimetres; negative values mean the water table sits below the surface
- peat_temp_c: peat temperature at 10 cm depth, in degrees Celsius

Rows that share a plot_id are repeat visits to one physical location rather
than separate locations, and readings from the same collar tend to resemble
each other.
