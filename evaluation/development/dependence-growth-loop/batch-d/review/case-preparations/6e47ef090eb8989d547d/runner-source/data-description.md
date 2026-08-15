# What data/input.csv contains

A glasshouse trial comparing two quinoa cultivars, Pasankalla and Titicaca, for
leaf-level photosynthetic performance. Twelve potted plants were raised under a
common light and irrigation regime, six plants of each cultivar. On every plant,
four tagged leaves at stem nodes 3, 5, 7 and 9 were measured once each with a
portable gas-exchange cuvette during a single mid-morning session. Each plant
therefore contributes four measurement rows to the table, and the table has 48
rows in total.

Columns:

- plant_id: tag of the potted plant that the measured leaf grew on. Twelve
  distinct plants appear, each on four rows.
- cultivar: the cultivar of that plant, either Pasankalla or Titicaca. All rows
  from a given plant carry the same value.
- leaf_node: stem node position of the measured leaf (3, 5, 7 or 9), counted from
  the base of the main stem.
- leaf_area_cm2: one-sided area of the measured leaf in square centimetres.
- assimilation_umol_m2_s: net CO2 assimilation rate of that leaf in micromoles of
  CO2 per square metre of leaf per second. This is the response of interest.

Because the four leaves on a plant share the same pot, root system and microclimate,
their assimilation values are more alike than values taken from different plants.

One row is: one tagged leaf measured once on one potted quinoa plant
Independent unit column: plant_id
