# Improved drought-tolerant maize versus local landrace: grain yield in one district

## Data description

The analysis uses one data file, `maize_trial.csv`. It is comma separated, has one header line and
40 data rows.

**One row is one smallholder farm.** The farm's whole maize field was harvested and weighed a single
time at the end of the season, so a row carries that farm's one and only yield figure. Each farm
appears exactly once: there are no repeat visits, no plots nested inside a farm and no second
season. The file holds 40 rows, 40 distinct farm codes and 40 farms. Rows, farms and independent
units are all the same 40. Each farm was allocated one seed type for its whole field, so no farm
appears in both groups.

The file has five columns, in this order.

| # | Column | Type | Units | What it holds |
| --- | --- | --- | --- | --- |
| 1 | `farm_id` | text | none | The farm's code in the district extension register, written `MKN-WW-NNN`: `MKN` is the district, `WW` is the ward (`03`, `05`, `07`, `11`) and `NNN` is the farm number in that ward. All 40 codes are distinct, one per farm. |
| 2 | `seed_type` | text | none | Which seed the farm planted, either `improved` or `landrace`. This is the grouping variable for the comparison. Twenty farms in each group. |
| 3 | `field_area_ha` | number | hectares | Area of the farm's maize field, to two decimals. Observed range 0.41 to 2.49 ha. Background information, not the outcome. |
| 4 | `season_rainfall_mm` | integer | millimetres | Total rainfall over the growing season at that farm, to the whole millimetre. Observed range 420 to 739 mm. Background information, not the outcome. |
| 5 | `grain_yield_t_ha` | number | tonnes per hectare | **The outcome.** Grain yield at fifteen percent moisture, from the single end-of-season weighing of the whole field, divided by the field area. Two decimals. Observed range 1.55 to 3.57 t/ha. |

The data are synthetic. They stand in for the described extension programme and are not measurements
from real farms.

## Methods

The question is whether mean grain yield differs between the two seed types. Because each farm gives
exactly one yield value and belongs to exactly one group, the 40 rows are 40 independent farms, and
every row goes straight into the test with no aggregation or averaging step first.

The test is an independent two-sample t-test on `grain_yield_t_ha`, comparing the `improved` group
with the `landrace` group. It is run in Welch's form, which does not assume the two groups have the
same spread. The test is two-sided at the five percent level. Alongside the p-value the analysis
reports each group's mean, standard deviation and standard error, the difference in means with a 95
percent confidence interval, and Cohen's d, a standardised effect size that expresses the gap
between the groups in units of the typical farm-to-farm spread.

Before testing, `analysis.py` checks the file against the design it assumes: that the number of rows
equals the number of distinct farms, that no farm carries more than one seed type, that no yield
value is missing and that `seed_type` has exactly two levels. All four checks pass. The script is
run with Python 3 using pandas and SciPy.

## Results

Sample size: 40 farms, 20 per seed group.

| Group | Farms | Mean yield (t/ha) | SD (t/ha) | SE (t/ha) | Min | Max |
| --- | --- | --- | --- | --- | --- | --- |
| `improved` | 20 | 3.076 | 0.366 | 0.082 | 2.35 | 3.57 |
| `landrace` | 20 | 2.060 | 0.346 | 0.077 | 1.55 | 2.90 |

The improved variety yielded 1.016 t/ha more on average than the landrace (95% confidence interval
0.788 to 1.244 t/ha). That is a 49.3 percent increase over the landrace mean of 2.060 t/ha.

Welch's two-sample t-test: t = 9.030, degrees of freedom = 37.88, two-sided p = 5.5e-11. Cohen's d =
2.86 against a pooled standard deviation of 0.356 t/ha.

**Conclusion.** The difference is statistically significant at the five percent level. Mean grain
yield was higher on the farms planting the improved drought-tolerant variety, and the confidence
interval keeps the true difference well above zero. The two group spreads are close to each other
(0.366 versus 0.346 t/ha), so the gap between the groups is much larger than the ordinary variation
between farms within a group.

## Recommendation for the extension programme

The improved variety is worth promoting in this district. A gain near 1 t/ha is large next to a
landrace baseline of about 2 t/ha, and even the cautious end of the confidence interval, 0.79 t/ha,
is a meaningful addition for a smallholder. The programme can move ahead with wider distribution of
the improved seed, paired with the extension advice farmers already receive.

Three limits should travel with that advice.

1. **One district, one season.** All 40 farms sit in the same district and shared one growing
   season, with rainfall from 420 to 739 mm. The result speaks to those conditions. Repeating the
   comparison in other districts and in a drier or wetter year would show whether the gain holds.
2. **Yield is not profit.** The comparison covers grain yield only. It says nothing about seed cost,
   whether the seed must be bought again each season, grain quality, taste or storage. A farmer's
   decision needs those figures too, and the programme should collect them.
3. **How farms were allocated is not recorded in the data.** The file shows which seed each farm
   planted, not how that assignment was made. If farms were not allocated at random, some of the gap
   could come from differences between the farms themselves rather than from the seed. The
   programme should confirm and document the allocation method before treating the 1.016 t/ha figure
   as the effect of the seed alone.

The background columns `field_area_ha` and `season_rainfall_mm` were carried through but not used in
the test, which is a plain comparison of the two groups as specified. They are available if a later,
pre-specified adjusted analysis is wanted.
