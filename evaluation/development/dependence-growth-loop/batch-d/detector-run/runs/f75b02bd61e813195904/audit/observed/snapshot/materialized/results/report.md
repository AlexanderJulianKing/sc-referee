# Chlorophyll a recovery in inoculated biocrust plots

## Monitoring data

- Long-format monitoring table: 48 plot-survey records from 12 restoration plots.
- Every plot was surveyed 4 times: one pre-inoculation baseline plus 3 follow-up surveys at 6, 12 and 18 months.
- Response: areal chlorophyll a density of the soil surface crust (mg m^-2).

## Reduction to independent units

Surveys repeated on the same plot are not independent observations of the
treatment, so the follow-up surveys of a plot are first averaged into a single
post-inoculation value. Each plot then contributes exactly one number to the
test, the plot-level change

    change = mean(follow-up surveys) - baseline survey.

The 12 plots were inoculated, tended and sampled separately and lie at least
200 m apart, so the plot-level changes are the independent replicates.

## Plot-level summary

| plot | baseline | follow-up mean | change |
| --- | --- | --- | --- |
| PLT-01 | 41.0 | 51.0 | +10.0 |
| PLT-02 | 56.0 | 62.0 | +6.0 |
| PLT-03 | 38.0 | 52.0 | +14.0 |
| PLT-04 | 63.0 | 67.0 | +4.0 |
| PLT-05 | 45.0 | 64.0 | +19.0 |
| PLT-06 | 52.0 | 61.0 | +9.0 |
| PLT-07 | 34.0 | 56.0 | +22.0 |
| PLT-08 | 59.0 | 66.0 | +7.0 |
| PLT-09 | 47.0 | 63.0 | +16.0 |
| PLT-10 | 50.0 | 61.0 | +11.0 |
| PLT-11 | 43.0 | 56.0 | +13.0 |
| PLT-12 | 55.0 | 73.0 | +18.0 |

All values are mg m^-2.

## Test and result

Exact two-sided Wilcoxon signed-rank test on the 12 plot-level changes; the
null hypothesis is that the change is distributed symmetrically about zero.

- plots analysed (one paired change each): 12
- plots that increased / decreased: 12 / 0
- mean baseline: 48.6 mg m^-2
- mean follow-up: 61.0 mg m^-2
- mean change: +12.4 mg m^-2
- median change: +12.0 mg m^-2 (range +4.0 to +22.0)
- signed-rank statistic W = 0.0, exact two-sided p = 0.000488

[selected-result] Crust chlorophyll a increased in 12 of 12 independently inoculated plots; the plot-level change (median +12.0 mg m^-2, mean +12.4 mg m^-2, n = 12 plots) differs from zero, exact two-sided Wilcoxon signed-rank test W = 0.0, p = 0.000488.

## Caveats

The design is a before-after comparison without untreated controls, so the
change cannot be separated from background seasonal recovery; the follow-up
surveys were also averaged rather than modelled, which discards information
about the shape of the recovery trajectory.
