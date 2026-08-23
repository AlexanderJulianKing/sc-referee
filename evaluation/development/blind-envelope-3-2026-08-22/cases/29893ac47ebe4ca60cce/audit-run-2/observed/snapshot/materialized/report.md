# Shading suppresses algal chlorophyll-a in intertidal rock pools

## Data description

The analysis uses one comma-separated file, `rockpool_chlorophyll.csv`, with a header line and 60
data rows.

**What one row represents.** One row is a single chlorophyll-a measurement taken at one of the five
fixed sampling points on the inner wall of one rock pool, eight weeks after the shading treatment
was set up.

**Columns.**

| Column | Type | Units | Description |
|---|---|---|---|
| `pool_id` | text | — | Identifier of the rock pool, `P01` through `P12`. |
| `treatment` | text | — | Shading treatment applied to the pool: `shaded` (mesh canopy fitted) or `uncovered` (left open to full ambient light). |
| `point_id` | text | — | Which of the five fixed sampling points around the pool's inner wall the measurement came from, `S1` through `S5`. |
| `chlorophyll_ug_cm2` | number | micrograms per square centimetre | Chlorophyll-a concentration of the algal film on the rock surface at that sampling point, per unit area of rock. |
| `surface_area_m2` | number | square metres | Surface area of the pool at low tide. |

There are no missing values; all 60 rows are complete in all five columns.

## Field design

Twelve separate intertidal rock pools were selected along one stretch of rocky coast. Six pools were
fitted with a mesh canopy that cuts incoming light, and six were left uncovered. Pool surface areas
at low tide ranged from 0.24 to 1.32 m2.

The canopies stayed in place for eight weeks. At the end of that period each pool was sampled at five
fixed points spread around its inner wall, and the chlorophyll-a concentration of the algal film was
measured at each point and expressed per unit area of rock. That gives 5 measurements from each of
the 12 pools, for 60 chlorophyll measurements in total: 30 from shaded pools and 30 from uncovered
pools.

## Methods

The data file was read into pandas and the chlorophyll-a values were split into two groups by the
`treatment` column. For each group we computed the mean, standard deviation, standard error, minimum
and maximum.

The effect of shading was tested with an independent two-sample t-test (Student's t, equal variances)
comparing chlorophyll-a between the shaded and uncovered groups, using `scipy.stats.ttest_ind`. Every
measurement row in the table was passed into the test as a separate observation, so the sample size
is n = 60 (30 per group) and the test has 58 degrees of freedom. We also report the difference in
means with its 95% confidence interval and Cohen's d as a standardised effect size. Analyses were run
in Python 3 with pandas 2.0.3 and scipy 1.9.1; the full script is `analysis.py`.

## Results

Sample size analysed: **n = 60** chlorophyll measurements, 30 shaded and 30 uncovered.

| Group | n | Mean (ug/cm2) | SD (ug/cm2) | SE (ug/cm2) | Min | Max |
|---|---|---|---|---|---|---|
| shaded | 30 | 4.05 | 1.38 | 0.25 | 1.63 | 6.59 |
| uncovered | 30 | 6.89 | 1.38 | 0.25 | 4.01 | 9.37 |

Shaded pools carried a mean chlorophyll-a concentration of 4.05 ug/cm2 against 6.89 ug/cm2 in
uncovered pools. The difference is -2.85 ug/cm2 (shaded minus uncovered), with a 95% confidence
interval of -3.56 to -2.13 ug/cm2. That is a drop of about 41% relative to the uncovered pools.

The independent two-sample t-test gave **t = -7.99 on 58 degrees of freedom, p = 6.3 x 10^-11**. The
standardised effect size was large, Cohen's d = -2.06, with a pooled standard deviation of
1.38 ug/cm2.

The two groups also separate cleanly at the level of the individual measurements: the highest shaded
value (6.59 ug/cm2) sits well below the top of the uncovered range (9.37 ug/cm2), and the lowest
uncovered value (4.01 ug/cm2) sits at roughly the shaded mean.

## Conclusion

Shading suppressed algal growth. Pools under a mesh canopy held 2.85 ug/cm2 less chlorophyll-a per
square centimetre of rock than uncovered pools after eight weeks, a reduction of about 41%, and the
difference was highly significant (t = -7.99, df = 58, p = 6.3 x 10^-11, n = 60). The size of the
effect, more than two pooled standard deviations, points to light availability as a strong control on
standing algal biomass on this shore over the growing period we sampled.
