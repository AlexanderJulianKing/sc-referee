# Alpine rock-glacier creep survey

A regional inventory catalogued 25 active rock glaciers in the crystalline
basement of one mountain range. Each landform occupies its own catchment, and
each was surveyed exactly once: a five-year satellite radar displacement field
was reduced to a single mean downslope creep velocity for that landform. No
landform was resurveyed and none appears twice, so the file holds 25 rows and
25 distinct landforms.

One row is: one rock glacier, surveyed once and summarised by a single mean creep velocity
Independent unit column: landform_id

Columns:

- landform_id: inventory code for the rock glacier; unique across the file.
- bedrock_class: lithology of the source headwall, either micaschist or
  orthogneiss.
- crest_elevation_m: elevation of the rooting zone in metres above sea level.
- mean_slope_deg: mean surface slope of the landform, in degrees.
- creep_velocity_cm_yr: mean downslope surface velocity, in centimetres per
  year.

The question is whether creep velocity differs between the two bedrock classes.
Because every landform contributes exactly one velocity and the landforms sit in
separate catchments, the rows are mutually independent and a row-independent
two-sample procedure is appropriate.
