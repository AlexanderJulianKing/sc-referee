# Warming raises soil CO2 efflux in a grassland field experiment

## Data description

All results below come from `soil_respiration.csv`. The file has 60 data rows plus a header. A
single row is one soil CO2 efflux reading taken at one collar inside one plot, together with the
soil temperature and soil moisture recorded at that same collar at the moment of the reading. A row
is therefore an individual measurement point, not a plot average.

The file has six columns:

- `plot_code` — the plot the reading came from, coded `P-101` through `P-110` (ten plots, six rows
  each).
- `warming_status` — the treatment of that plot, either `ambient` or `warmed`.
- `collar_position` — which of the six fixed collars in the plot produced the reading, `C1` through
  `C6`.
- `soil_temp_c` — soil temperature at 5 cm depth at that collar, in degrees Celsius.
- `soil_moisture_pct` — volumetric water content at that collar, as a percentage.
- `co2_efflux` — soil CO2 efflux at that collar, in micromoles of CO2 per square metre per second.
  This is the response variable.

Rows are ordered plot by plot, and within each plot by collar position, in the order they were
collected. There are no missing values.

## Site and design

The experiment is a grassland warming study with ten plots, each 2 m by 2 m. Five plots (P-102,
P-103, P-106, P-108, P-109) carry active infrared heaters that hold the soil roughly 2 degrees
Celsius above ambient. The other five (P-101, P-104, P-105, P-107, P-110) carry dummy heater frames
and act as controls. Heater assignment is interleaved across the plot numbering rather than blocked.
Six fixed collars were installed in every plot, and the technician read all six collars in every
plot on the same summer morning, giving 60 readings in total.

The heaters performed as intended. Mean soil temperature at 5 cm was 20.04 degrees Celsius in the
warmed plots against 17.93 degrees Celsius in the controls, a gap of 2.11 degrees. Mean soil
moisture was similar in the two conditions, 22.1 percent under warming and 23.3 percent under
ambient conditions.

## Comparison performed

I compared soil CO2 efflux between the warmed and ambient conditions with a two-sample t-test
(`scipy.stats.ttest_ind`, two-sided, equal variances assumed).

The measurements that entered the test were the individual collar readings from the `co2_efflux`
column. Every reading from a warmed plot was placed in the warmed sample and every reading from an
ambient plot was placed in the ambient sample. No averaging or aggregation was applied before the
test, and no readings were excluded. The sample sizes I am claiming are therefore **N = 30 readings
in the warmed condition and N = 30 readings in the ambient condition, 60 readings in total**, which
gives 58 degrees of freedom.

## Results

Soil CO2 efflux was higher under warming. The warmed condition averaged 3.19 micromoles of CO2 per
square metre per second (SD 0.83, N = 30 readings), and the ambient condition averaged 2.62
micromoles per square metre per second (SD 0.38, N = 30 readings). The difference between the two
means is 0.57 micromoles per square metre per second, an increase of about 22 percent over the
control level.

The t-test gives t = 3.44 with 58 degrees of freedom and p = 0.0011.

## Conclusion

Warming the soil by roughly 2 degrees Celsius raised soil CO2 efflux by about 0.57 micromoles of
CO2 per square metre per second relative to unheated controls, and the difference is statistically
significant at p = 0.0011. The result is consistent with a direct temperature stimulation of soil
respiration in this grassland, and the similar moisture levels in the two conditions indicate that
the effect is not driven by a difference in soil water content.
