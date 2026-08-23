# Data description

The data file is `soil_respiration.csv`. It holds the soil respiration survey from the grassland
warming experiment, collected across one summer morning.

## What one row represents

One row is **a single soil CO2 efflux reading taken at one collar inside one plot**. It is one
measurement point, not a plot summary. Each row also carries the soil temperature and soil moisture
recorded at that same collar at the time of the reading.

## Units and counts

- 10 experimental plots, each 2 m by 2 m (`P-101` through `P-110`).
- 6 fixed collar positions inside every plot (`C1` through `C6`).
- 6 readings per plot x 10 plots = **60 rows** of data, plus one header row.
- Rows are ordered plot by plot, and within each plot by collar position, in collection order.

## The two groups

Warming was applied to whole plots. Of the 10 plots:

- **ambient** (5 plots: P-101, P-104, P-105, P-107, P-110): dummy heater frames, no heat applied.
  30 readings in total.
- **warmed** (5 plots: P-102, P-103, P-106, P-108, P-109): active infrared heaters holding the soil
  about 2 degrees Celsius above ambient. 30 readings in total.

Heater assignment was interleaved across the plot numbering rather than blocked.

## Columns

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `plot_code` | string | - | The plot the reading came from, `P-101` through `P-110`. Ten distinct values, 6 rows each. |
| `warming_status` | string | - | Treatment of that plot, either `ambient` or `warmed`. Constant within a plot. |
| `collar_position` | string | - | Which of the six fixed collars in that plot the reading came from, `C1` through `C6`. |
| `soil_temp_c` | float, 2 dp | degrees Celsius | Soil temperature at 5 cm depth at that collar. |
| `soil_moisture_pct` | float, 1 dp | percent | Volumetric water content at that collar. |
| `co2_efflux` | float, 2 dp | micromoles CO2 per square metre per second | Soil CO2 efflux at that collar. This is the outcome of interest. |

## Notes on the values

Plots differ from one another for reasons that have nothing to do with the heaters, such as soil
depth, root density, drainage, and microtopography. Because of that, the six collars inside one plot
give readings that are similar to each other, and the plot-to-plot spread in baseline efflux is at
least as large as the average difference between warmed and ambient plots. There are no missing
values in the file.

The file was produced by `make_data.py` with a fixed random seed (20260821), so re-running that
script reproduces the CSV exactly.
