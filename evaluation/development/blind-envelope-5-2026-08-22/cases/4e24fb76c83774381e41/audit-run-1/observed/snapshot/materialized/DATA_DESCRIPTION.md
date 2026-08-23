# Data description

Two comma-separated files describe one summer of butterfly transect walks on farmland. Both were
written by `make_data.py`, which uses a fixed random seed, so re-running it reproduces them exactly.

## Study units and groups

- **Units:** 22 fixed walking routes (transects).
- **Groups:** the `management` column splits the routes into two management regimes.
  - `wildflower_margin` — 11 routes crossing farms in a wildflower-margin scheme.
  - `conventional` — 11 routes crossing conventionally managed farms.
- **Survey effort:** every route was walked once a week for 18 weeks by the same recorder, so all
  22 routes have the full 18 weekly visits and none are missing.
- **Route codes:** transect-register style, e.g. `UKBMS-0412`. Each code appears on exactly one
  route, and the code carries no hint of which group the route is in.

## File 1: `weekly_counts.csv` — the weekly file

396 data rows plus one header row. **One row is one route-week**: a single walk of one route in one
week (22 routes x 18 weeks = 396).

| Column | Type | Description |
| --- | --- | --- |
| `route_code` | text | Register code of the route walked. Repeats 18 times, once per week. |
| `management` | text | Management regime of that route: `wildflower_margin` or `conventional`. Constant within a route. |
| `survey_week` | integer | Week of the survey season, 1 through 18. Week 1 is the first week walked. |
| `air_temp_c` | decimal | Air temperature in degrees Celsius recorded at the start of that walk. Ranges 14.0 to 28.0, warmest around the midsummer weeks. |
| `butterfly_count` | integer | Number of butterflies of all species counted along the route on that walk. Ranges 5 to 45 on conventional routes and 11 to 80 on wildflower-margin routes. Counts rise to a midsummer peak near week 10 and fall away again, and each route keeps its own consistent level across the season. |

## File 2: `route_summary.csv` — the per-route file

22 data rows plus one header row. **One row is one route**, summarising that route's whole season.
Nothing else is in this file.

| Column | Type | Description |
| --- | --- | --- |
| `route_code` | text | Register code of the route. Appears exactly once. Same 22 codes as the weekly file. |
| `management` | text | Management regime of that route: `wildflower_margin` or `conventional`. |
| `weeks_surveyed` | integer | Number of weekly walks contributing to that route's mean. 18 for every route. |
| `mean_weekly_count` | decimal | That route's mean butterfly count per walk, rounded to 2 decimal places. Route means run 12.56 to 26.17 on conventional routes and 28.83 to 47.72 on wildflower-margin routes. |

## How the two files agree

`route_summary.csv` is computed directly from the rows of `weekly_counts.csv`. For every route,
`weeks_surveyed` equals the number of weekly rows carrying that `route_code`, and
`mean_weekly_count` equals the mean of those rows' `butterfly_count` values rounded to 2 decimals.
The route codes and the `management` label of each route match across the two files.
