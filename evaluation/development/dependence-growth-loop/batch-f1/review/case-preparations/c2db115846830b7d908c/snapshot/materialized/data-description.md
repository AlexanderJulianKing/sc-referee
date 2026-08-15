# What is in data/input.csv

The file records a night-time amphibian survey of urban stormwater ponds run
across one frog breeding season. A field crew visited each pond once, waited
through dusk, and logged the moment continuous calling started at that pond.

One row is: one urban stormwater pond, described by the single night on which it was surveyed

Independent unit column: pond_id

## Columns

- pond_id: unique code for the pond; each code occurs on exactly one line.
- survey_date: calendar date of that pond's one and only visit.
- lighting_regime: "lit" when permanent street lighting falls on the pond margin, "unlit" otherwise.
- pond_area_ha: open-water surface area in hectares, traced from aerial imagery.
- water_temp_c: water temperature in degrees Celsius, taken on arrival.
- chorus_onset_min_after_sunset: minutes between local sunset and the start of continuous calling.

## How independence works here

Twelve ponds contribute twelve lines, one apiece. No pond was revisited, no
pond is split across lines, and no two ponds were surveyed on the same date,
so every onset value comes from a different source. Ponds are separate water
bodies in separate catchments and were not paired or matched with each other.
A procedure that treats the lines as independent observations therefore suits
this table, and the grouping variable (lighting regime) varies between ponds
rather than within any pond.
