# Total phosphorus and catchment land use in sixteen regional lakes

## 1. Data description

All results below come from one file, `lake_phosphorus.csv`, which has a header row and 96 data
rows. The values are invented for this project and are not measurements from a real survey.

**What one row represents.** One row is a single water sample taken at one open-water station in one
lake: one total phosphorus measurement, the water depth at that station, and the two attributes that
belong to the lake as a whole. A row is not a lake. Sixteen lakes were surveyed and six stations
were sampled in each, so 16 x 6 = 96 rows. The six rows that share a `lake_id` are spatial
subsamples of the same lake.

The six columns, in file order:

| Column | Type | Units | Varies at | Description |
|---|---|---|---|---|
| `lake_id` | text | none | lake | Lake identifier, `L01` through `L16`. Repeated across the six rows of a lake. This column marks which rows belong to the same lake. |
| `catchment_land_use` | text | none | lake | Predominant land use of the surrounding catchment, either `agricultural` or `forested`. Constant within a lake. |
| `station_number` | integer | none | station | Which of the six open-water stations the sample came from, 1 to 6. A label only. Station 3 in one lake has no relation to station 3 in another, and the numbering carries no order or gradient. |
| `total_phosphorus_ug_l` | number, 1 decimal | micrograms per litre | station | Total phosphorus in the water sample. This is the response variable. |
| `water_depth_m` | number, 1 decimal | metres | station | Water depth at the sampling station. |
| `lake_area_ha` | number, 1 decimal | hectares | lake | Surface area of the whole lake. Constant across the six rows of a lake, so 16 distinct values are spread over 96 rows. |

There are no missing values and no duplicated rows. The analysis script checks all of this on load,
including that `catchment_land_use` and `lake_area_ha` really are constant within each lake.

`water_depth_m` and `lake_area_ha` are recorded as survey context. Neither enters the comparison
reported here.

## 2. Survey design

Sixteen lakes in one region were surveyed. Eight have predominantly agricultural catchments (`L01`
to `L08`) and eight have predominantly forested catchments (`L09` to `L16`). At each lake, water was
collected at six stations spread across the open-water zone, and total phosphorus was measured in
every sample. The design is balanced: eight lakes per group, six stations per lake, 48 samples per
group.

The independent unit is the lake. Catchment land use is a property of the whole catchment and
therefore of the whole lake, so land use is assigned at the lake and cannot vary from station to
station. The six samples from one lake are repeated measures on that lake. They tell us how
uniformly phosphorus is mixed across that lake's open water, and they sharpen the estimate of that
lake's mean, but they do not add lakes to the comparison.

**Sample size: 16 lakes contributing 96 samples.**

The data bear the dependence out. Splitting the variation that remains after removing the two
land-use means gives a between-lake standard deviation of 6.79 ug/L and a station-to-station
standard deviation within a lake of 4.43 ug/L, an intraclass correlation of 0.70. In plain terms,
about seven-tenths of the leftover variance sits between lakes rather than within them. Two samples
from the same lake are much more alike than two samples drawn from different lakes in the same
land-use group, so the 96 samples carry far less independent information than 96 unrelated samples
would.

## 3. Primary method

The primary inference resamples whole lakes. The analysis first reduces each lake to its mean of six
stations, which leaves 16 lake means, eight per group. Every resampling step below moves entire
lakes, never individual water samples, so the dependence among the six stations inside a lake is
carried along rather than assumed away.

Two lake-level procedures are used together.

**Null distribution: exact permutation of land-use labels across lakes.** The null hypothesis of
interest is that catchment land use is unrelated to a lake's phosphorus level. Under that
hypothesis, any eight of the 16 lakes could equally well have carried the agricultural label. There
are C(16, 8) = 12870 such assignments, few enough to enumerate completely, so the analysis evaluates
all of them and no random draws are needed. The two-sided p-value is the fraction of assignments
whose absolute difference in group means is at least as large as the observed one. Because the
enumeration is exhaustive, this p-value is exact for this design and is reproducible without a seed.

**Interval: cluster bootstrap.** Uncertainty in the difference is estimated by resampling whole
lakes with replacement within each group, 8 agricultural and 8 forested per resample, recomputing
the two group means from the resampled lakes, and taking percentiles of the resulting differences.
This uses 20000 resamples with a fixed seed of 20260822.

The reasoning behind this choice is straightforward. A standard two-sample test on the individual
samples assumes the observations are independent, and here they are not. Permuting labels at the
lake level respects the fact that land use was assigned at the lake, and resampling whole lakes
propagates both sources of variation, between lakes and between stations within a lake, into the
interval. Neither procedure needs a distributional assumption about phosphorus, which is useful
because the forested lake means lean mildly right-skewed. With only 16 lakes, the exhaustive
permutation also avoids relying on a large-sample approximation.

The smallest p-value this design can attain is 2 / 12870 = 0.00016. No procedure applied to eight
lakes per group can report a smaller one, and that floor is a property of the survey size, not of
the analysis.

## 4. Primary result

| Quantity | Value |
|---|---|
| Sample size | 16 lakes contributing 96 samples |
| Mean of the 8 agricultural lake means | 32.70 ug/L |
| Mean of the 8 forested lake means | 12.19 ug/L |
| Difference (agricultural minus forested) | 20.51 ug/L |
| Exact lake-level permutation test, two-sided | p = 0.00047 (6 of 12870 assignments) |
| Cluster bootstrap standard error | 3.26 ug/L |
| Cluster bootstrap 95% percentile interval | 13.99 to 26.74 ug/L |

Lakes with predominantly agricultural catchments carry higher total phosphorus than lakes with
predominantly forested catchments. The difference between the two group means, computed at the lake
level, is 20.5 ug/L, and a comparison this large or larger arises in only 6 of the 12870 possible
ways of assigning the land-use labels across the 16 lakes. The cluster bootstrap interval runs from
about 14 to about 27 ug/L, so the data are consistent with a difference between about 1.1 and
2.2 times the forested group's own mean level, and not with no difference at all.

The interval is wide because 16 lakes is a small survey and lakes within a group genuinely differ
from one another. The eight agricultural lake means run from 22.4 to 45.5 ug/L and the eight
forested means from 6.1 to 26.5 ug/L, so the two groups overlap at their edges even though their
centres are far apart. Adding more stations to the existing lakes would narrow the estimate of each
lake's own mean, but it would not narrow this comparison much. Only more lakes would do that.

This result concerns the two land-use categories as they occur in these sixteen lakes. Lakes were
surveyed as they were found, not assigned to a catchment type, so the comparison is observational.
Catchment land use travels with other things such as soil, slope, and hydrology, and the survey
cannot separate phosphorus loading from agriculture itself from whatever else accompanies it in
these catchments.

## 5. Illustrative row-level contrast, which is not the inferential result

For contrast, the script also computes a plain Welch two-sample t-test across all 96 individual
samples, 48 in each group, and prints it in a separately marked block.

| Quantity | Value |
|---|---|
| Mean difference across individual samples | 20.51 ug/L |
| t | 12.891 |
| Approximate degrees of freedom | 92.22 |
| Two-sided p | 2.4e-22 |

**This row-level comparison is not a valid basis for inference in this survey, and it is not the
result of this study.** It should not be read as one, cited as one, or compared with the primary
p-value as though the two were competing estimates of the same thing. It is reported only to show
what the invalid analysis produces here.

The reason it is invalid is the design. The test treats the 96 samples as 96 independent
observations, and they are not independent: six of them come from each lake, and those six share
whatever makes that lake nutrient-rich or nutrient-poor. The intraclass correlation of 0.70
quantifies how strongly. Land use was never assigned station by station, so the six stations in a
lake cannot serve as six separate pieces of evidence about land use. They are six looks at one
lake.

The consequence is visible in the numbers. The point estimate happens to match the lake-level
difference of 20.51 ug/L, because the design is balanced and every lake contributes the same six
stations. What differs is the uncertainty. The t-test spends about 92 degrees of freedom where the
design supplies 14, which inflates the apparent precision and drives the p-value down by about
eighteen orders of magnitude relative to the exact lake-level test. The conclusion, that
agricultural-catchment lakes are higher in phosphorus, survives the correct analysis in this
particular data set. That is a fact about how large the effect is here, not a defence of the
row-level test. With a smaller difference between land-use types, the same error could easily turn
an inconclusive survey into an apparently decisive one.

## 6. Reproducing the analysis

From the project folder:

```
/usr/local/bin/python3 analysis.py
```

The script reads `lake_phosphorus.csv`, prints the design summary, the descriptive summaries at both
the sample and lake levels, the variance components, the primary lake-level result, and the
illustrative row-level contrast in its own marked block. The permutation test is exhaustive and so
returns the same p-value every run. The bootstrap uses the fixed seed 20260822, so its interval
reproduces exactly as well.
