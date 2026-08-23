# Data description

## The file

There is one data file, `lake_phosphorus.csv`. It has a single header row and 96 data rows.

The values are invented for this project, not measured. They were produced by `make_data.py`
(standard library only, fixed seed `20260822`), which rewrites the CSV exactly as distributed when
re-run with `/usr/local/bin/python3 make_data.py`.

No second summary file is included. The survey is small enough that every station value is carried
in the one file, and the lake-level means the analysis needs are computed from it rather than stored
separately.

## What one row represents

One row is **one water sample from one sampling station in one lake**: a single total phosphorus
measurement, together with the depth of the water at that station and the two attributes that belong
to the lake as a whole (its catchment land use and its surface area).

A row is *not* a lake. Sixteen lakes were surveyed, six stations were sampled in each, and each
station contributes one row, so 16 x 6 = 96 rows. The six rows sharing a `lake_id` are spatial
subsamples from the open-water zone of the same lake. They are repeated measures on that lake, not
six independent lakes, and the analysis has to treat them that way.

Units of observation, stated plainly:

| Level | Count | What it is |
|---|---|---|
| Lake (the independent unit) | 16 | 8 agricultural catchment, 8 forested catchment |
| Station (the row) | 96 | 6 per lake, 48 per land-use group |

## The two groups

The grouping variable is `catchment_land_use`, and it is a property of the lake, so it is constant
across all six rows of a lake. It takes exactly two values:

- `agricultural` — 8 lakes (`L01`-`L08`), 48 rows. Catchment predominantly agricultural.
- `forested` — 8 lakes (`L09`-`L16`), 48 rows. Catchment predominantly forested.

The design is balanced: equal numbers of lakes per group and equal numbers of stations per lake.

## Columns

Six columns, in file order. Headers are lowercase words joined by underscores.

| Column | Type | Units | Varies at | Description |
|---|---|---|---|---|
| `lake_id` | text | — | lake | Lake identifier, `L01` through `L16`. Repeats across the six rows of a lake; this is the column that marks which rows are dependent on each other. |
| `catchment_land_use` | text | — | lake | Predominant land use of the surrounding catchment. Either `agricultural` or `forested`. Constant within a lake. |
| `station_number` | integer | — | station | Which of the six open-water sampling stations in that lake the sample came from, 1 to 6. It is a label, not a measurement: station 3 in one lake has nothing to do with station 3 in another, and the numbering carries no order or gradient. |
| `total_phosphorus_ug_l` | number, 1 decimal | micrograms per litre (ug/L) | station | Total phosphorus in the water sample. This is the response variable. |
| `water_depth_m` | number, 1 decimal | metres | station | Water depth at that sampling station. |
| `lake_area_ha` | number, 1 decimal | hectares | lake | Surface area of the whole lake. Constant across the six rows of a lake, so there are 16 distinct values spread over 96 rows, not 96. |

There are no missing values, and no row is duplicated.

## How the values were built, and what they came out as

Total phosphorus was generated as a lake-level mean plus station-level noise, which is what creates
the within-lake dependence the design has to respect. The generator aimed at an agricultural mean
near 34 ug/L, a forested mean near 12 ug/L, a between-lake spread near 9 ug/L, and a station-to-
station spread near 4 ug/L.

The realised values in the delivered file, which are what the analysis will actually see:

| Quantity | Agricultural | Forested |
|---|---|---|
| Lakes / rows | 8 / 48 | 8 / 48 |
| Mean of the 96 individual samples | 32.7 ug/L | 12.2 ug/L |
| SD across individual samples | 8.3 ug/L | 7.2 ug/L |
| Median sample | 30.8 ug/L | 11.4 ug/L |
| Range of individual samples | 11.2 - 53.3 ug/L | 2.4 - 32.5 ug/L |
| Range of the 8 lake means | 22.4 - 45.5 ug/L | 6.1 - 26.5 ug/L |
| SD of the 8 lake means | 7.7 ug/L | 6.3 ug/L |

Pooled across both groups: the between-lake SD is 7.0 ug/L and the within-lake (station-to-station)
SD is 4.4 ug/L. Roughly 0.7 of the leftover variance sits between lakes rather than within them.
That is the practical reason the six stations in a lake cannot be counted as six independent
measurements: they are far more alike than two samples drawn from different lakes in the same group.
The difference between the group means, computed at the lake level, is 20.5 ug/L.

Two departures from a plain normal draw are worth stating, because they are deliberate and they show
up in the numbers above:

1. **Lake means are truncated below.** Phosphorus is a concentration and cannot be negative, and a
   clear forested lake here does not sit below about 3 ug/L. A normal draw with a mean of 12 and an
   SD of 9 puts real probability mass below zero, so the eight means in a group were redrawn as a
   block until all cleared that floor and the group mean and spread landed near target. This is why
   the realised forested between-lake SD (6.3) sits under the nominal 9, and why the forested group
   leans mildly right-skewed.
2. **Lake area is kept independent of land use.** Areas were drawn for both groups from one common
   5-300 ha range, and the block of 16 was redrawn until the groups overlapped across that range.
   Left unconstrained, a chance draw can hand the two groups nearly separate size ranges, which
   would quietly turn surface area into a stand-in for catchment type and confound the very
   comparison the survey is about. Station depth is derived from lake area, so constraining area
   keeps depth unconfounded too.

Realised ranges for the two covariates: `lake_area_ha` runs 12.0 - 292.1 ha (group means 166 ha
agricultural, 153 ha forested), and `water_depth_m` runs 2.4 - 12.3 m with a mean of 6.8 m. Larger
basins are on average deeper, with scatter, and depth varies from station to station inside a lake.
