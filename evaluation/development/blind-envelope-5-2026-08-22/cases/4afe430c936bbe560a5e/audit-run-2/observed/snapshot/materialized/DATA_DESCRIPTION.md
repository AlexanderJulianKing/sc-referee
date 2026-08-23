# Data description

## The file

`maize_trial.csv` is the only data file in this project. It is comma separated, with one header line
and 40 data rows.

It was written by `make_data.py` (Python standard library only, fixed random seed `20260822`), so
re-running that script reproduces the same file exactly.

## What one row represents

One row is **one smallholder farm**. The farm's whole maize field was harvested and weighed a single
time at the end of the season, so a row carries that farm's one and only yield measurement.

Each farm appears exactly once. There are no repeat visits, no plots nested inside a farm, and no
second season. That means the number of rows, the number of farms, and the number of independent
units are all the same number: 40.

## Units and rows

| Count | Value |
| --- | --- |
| Farms (independent holdings) | 40 |
| Data rows | 40 |
| Rows per farm | 1 |
| Yield measurements per farm | 1 |

## The two groups

All 40 farms are in one district and took part in the same extension programme season. They were
split into two seed groups of equal size:

| `seed_type` | Meaning | Farms |
| --- | --- | --- |
| `improved` | Farm was allocated the improved drought-tolerant maize variety | 20 |
| `landrace` | Farm continued with its own local landrace seed | 20 |

A farm belongs to exactly one group. No farm grew both seed types, so the two groups share no farms
and the comparison between them is between separate, independent farms.

## Columns

Columns appear in the file in this order.

| # | Column | Type | Units | Description |
| --- | --- | --- | --- | --- |
| 1 | `farm_id` | text | none | The farm's code in the district extension register, formatted `MKN-WW-NNN`, where `MKN` is the district, `WW` is the ward (`03`, `05`, `07`, `11`), and `NNN` is the farm number inside that ward. Unique across the file: 40 codes for 40 farms. |
| 2 | `seed_type` | text | none | Which seed the farm planted. Exactly two values: `improved` or `landrace`. This is the grouping variable for the comparison. |
| 3 | `field_area_ha` | number | hectares | Area of the farm's maize field, recorded to two decimals. Ranges from 0.41 to 2.49 ha. Background information about farm size; it is not the outcome. |
| 4 | `season_rainfall_mm` | integer | millimetres | Total rainfall recorded over the growing season at that farm, rounded to a whole millimetre. Ranges from 420 to 739 mm. Background information about growing conditions; it is not the outcome. |
| 5 | `grain_yield_t_ha` | number | tonnes per hectare | **The outcome.** Grain yield at fifteen percent moisture, from the single end-of-season weighing of the whole field, divided by the field area. Rounded to two decimals. Ranges from 1.55 to 3.57 t/ha across all farms. |

## Values as generated

These are the values in the file as written, for reference only. The analysis has not been run yet
and no test has been carried out.

| Group | Farms | Mean yield (t/ha) | Standard deviation (t/ha) | Min | Max |
| --- | --- | --- | --- | --- | --- |
| `landrace` | 20 | 2.06 | 0.35 | 1.55 | 2.90 |
| `improved` | 20 | 3.08 | 0.37 | 2.35 | 3.57 |

## How the numbers were built

`make_data.py` draws each farm independently:

- Field area is uniform between 0.4 and 2.5 ha.
- Season rainfall is a normal draw centred on 600 mm with a standard deviation of 78 mm, clipped to
  the 420 to 780 mm window.
- Yield is a normal draw around the group's mean (2.15 t/ha for landrace, 3.05 for improved), plus a
  small rainfall term of 0.0018 t/ha for each millimetre the farm's rainfall sits above the 600 mm
  district average, then clipped to the plausible window for its group (1.4 to 3.0 for landrace, 2.2
  to 4.1 for improved) and rounded to two decimals.

Register codes are shuffled and seed allocation is shuffled separately, so seed type is not tied to
ward or to a farm's position in the register.

The data are synthetic. They stand in for the described extension programme and are not measurements
from real farms.
