# What is in data/input.csv

Twenty-four drained upland peat basins were surveyed once each during the 2025
growing season as part of a rewetting programme. Twelve of the basins had their
drainage ditches dammed with peat blocks before the survey; the other twelve
were left with their ditches open. A surveyor walked each basin a single time
and recorded whether Sphagnum moss had re-established across the basin floor,
along with the basin's mapped area and its mean peat depth.

One row is: one drained peat basin, surveyed a single time, with its ditch treatment and its yes/no Sphagnum re-establishment outcome

Independent unit column: basin_id

Columns

- basin_id: the survey code for the basin. Every code appears exactly once, so
  the file has as many rows as there are basins.
- catchment: the named catchment the basin sits in. Descriptive only.
- ditch_treatment: "blocked" if the drainage ditches were dammed, "open" if they
  were not. The treatment applies to the whole basin and does not change within
  a basin.
- basin_area_ha: mapped area of the basin in hectares.
- peat_depth_cm: mean peat depth across the basin, in centimetres.
- sphagnum_reestablished: "yes" or "no", the single outcome recorded for that
  basin at its one survey visit.

Because every basin contributes exactly one row and no basin was visited twice,
the rows can be treated as independent observations, and the yes/no counts can
go straight into a two-by-two comparison of blocked against open basins.
