# Kettle Creek terrace groundwater monitoring data

This note describes `data/input.csv`, the nitrate record collected from eighteen
shallow monitoring wells on the Kettle Creek terrace before and after a riparian
wetland was reconnected to its floodplain.

Every well was visited on six survey rounds: three rounds in the baseline year
(study days 12, 40 and 68) and three rounds in the first post-restoration year
(study days 215, 243 and 271). The table is kept in long format, so a single well
contributes six rows, one per visit, and the file holds 108 data rows beneath a
single header row.

One row is: one water sample drawn from one monitoring well on one survey round
Independent unit column: well_id

The eighteen wells are the independent units of the study. The six rounds
recorded for a given well are repeated measurements of the same piece of aquifer
and are not independent of one another, so an analysis that reports a claim about
the restoration should reduce each well to a single value (for example a
baseline-to-post change score) before comparing units.

## Columns

- `well_id` - identifier of the monitoring well, W-01 to W-18. Repeated on the six rows belonging to that well.
- `screen_depth_m` - depth of the middle of the well screen below ground surface, in metres. A fixed property of the well, so it is constant within a well_id.
- `period` - `baseline` for rounds collected before reconnection, `post_restoration` for rounds collected afterwards.
- `survey_round` - label of the survey campaign, R1 to R6.
- `study_day` - day of the study on which that round was sampled, counted from the start of baseline monitoring.
- `nitrate_mg_per_l` - nitrate concentration of the sample, in milligrams of nitrate-N per litre.

## Reading notes

Concentrations were measured by ion chromatography on filtered samples and are
reported to one decimal place. There are no missing values and no ragged rows:
each of the eighteen wells has exactly three baseline rows and three
post-restoration rows.
