# Raised potassium and butterhead lettuce head fresh mass

A nutrient-film glasshouse trial, harvested 15-16 June 2026

## Aim

The grower wanted to know whether a nutrient formulation with raised potassium
produces heavier butterhead lettuce heads than the standard formulation
currently in use, and whether any gain is large enough to be worth adopting for
the main crop.

## Growing setup

The glasshouse holds ten nutrient-film growing gutters. Each gutter has its own
reservoir and its own dosing line, so each gutter is fed one formulation for the
whole crop. Five gutters were dosed with the standard formulation (G01, G03,
G05, G07, G09) and five with the raised-potassium formulation (G02, G04, G06,
G08, G10). The two formulations were interleaved across the house rather than
banked at one end, so neither treatment sat entirely in the warmer or cooler
part of the glasshouse.

Every gutter carries twelve plant positions along its length, numbered from the
dosing end (position 1) to the far end (position 12). At harvest each of the
twelve heads in every gutter was cut and weighed fresh on the morning of
harvest, to 0.1 g. That gives 120 harvested heads in total: 60 grown on the
standard formulation and 60 grown on the raised-potassium formulation. No head
was lost; every one of the 120 plant positions was cut and weighed.

Cutting was spread over two mornings. Gutters G01-G05 were cut on 15 June 2026
and gutters G06-G10 on 16 June 2026.

## Method

The analysis is carried out by `analysis.py` at the project root, which reads
`lettuce_harvest.csv`.

The script first summarises head fresh mass under each formulation: the number
of harvested heads, the mean, the standard deviation, the standard error, and
the minimum, median and maximum head mass.

It then compares head fresh mass between the two formulations with an
independent two-sample t-test assuming equal variances. Every harvested head is
entered as its own observation, so the sample size for each formulation is the
total number of harvested heads grown on that formulation: 60 heads per
formulation, giving 118 degrees of freedom. Alongside the test the script
reports the difference in mean head mass, the pooled standard deviation, the
standard error of the difference, a 95% confidence interval for the difference,
and Cohen's d as a measure of effect size.

## Results

### Head fresh mass by formulation

| Formulation      | Heads weighed | Mean (g) | SD (g) | SE (g) | Min (g) | Median (g) | Max (g) |
|------------------|---------------|----------|--------|--------|---------|------------|---------|
| standard         | 60            | 244.33   | 46.65  | 6.02   | 169.2   | 240.8      | 356.8   |
| raised potassium | 60            | 276.64   | 34.86  | 4.50   | 203.4   | 273.9      | 362.8   |

### Comparison of the two formulations

| Quantity                                   | Value                |
|--------------------------------------------|----------------------|
| Sample size, raised potassium              | 60 harvested heads   |
| Sample size, standard                      | 60 harvested heads   |
| Difference in mean head mass               | +32.31 g             |
| Relative change against standard           | +13.22 %             |
| Pooled standard deviation                  | 41.18 g              |
| Standard error of the difference           | 7.52 g               |
| 95% confidence interval for the difference | +17.42 g to +47.19 g |
| t (118 df)                                 | 4.297                |
| p-value                                    | 0.00003576           |
| Cohen's d                                  | 0.785                |

Heads grown on the raised-potassium formulation averaged 276.64 g against
244.33 g on the standard formulation, a gain of 32.31 g per head, or 13.22 %.
The difference is statistically significant at the 5 % level
(t(118) = 4.297, p = 0.00003576). The 95 % confidence interval runs from
+17.42 g to +47.19 g, so the whole interval sits above zero. Cohen's d of 0.785
places the size of the difference in the moderate-to-large range.

Head mass was also more even under the raised-potassium formulation. The
standard deviation was 34.86 g against 46.65 g on the standard formulation, and
the lightest head cut was 203.4 g against 169.2 g. A tighter spread matters
commercially, because heads that fall below the pack minimum are downgraded.

## Recommendation to the grower

The raised-potassium formulation is worth adopting for the next butterhead crop.
It produced heads about 32 g heavier on average, a gain of a little over 13 %,
and the confidence interval says the true gain is unlikely to be smaller than
about 17 g per head. On a house of this size that is a meaningful lift in
saleable mass, and the narrower spread of head masses should also reduce the
proportion of undersized heads.

Two practical points go with that recommendation.

First, cost the change before switching the whole house. The gain per head has
to cover the extra potassium salt and any change in dosing routine. At 13 % more
fresh mass per head the margin is likely to be comfortable, but the arithmetic
depends on the grower's own input prices and pack-out grades.

Second, watch the far end of the gutters. Heads at positions further from the
dosing end ran a little lighter than heads near the dosing end, which is the
pattern expected from nutrient depletion along the channel. This showed under
both formulations, so it is a question of flow rate and dosing rather than of
which formulation is used. Raising the recirculation rate, or shortening the
run before the return, would be worth trialling separately.

A sensible next step is to repeat the comparison on the following crop, and at
the same time trial the recirculation change, so that both the formulation gain
and the along-channel gradient are covered.

## Data description

### File

`lettuce_harvest.csv` - the harvest record for the trial. 120 data rows plus one
header row.

### What one row represents

One row is one harvested lettuce head: a single plant, cut at one plant position
in one nutrient-film gutter, weighed fresh on the day of harvest. There are 120
rows because 10 gutters x 12 plant positions = 120 heads were cut and weighed.

### Columns

| Column                  | Type            | Units / values                                | Meaning                                                                               |
|-------------------------|-----------------|-----------------------------------------------|---------------------------------------------------------------------------------------|
| `gutter_code`           | text            | `G01` ... `G10`                               | Identifier of the nutrient-film gutter the head was grown in.                          |
| `formulation`           | text, 2 levels  | `standard`, `raised_potassium`                | Nutrient formulation dosed to that gutter's reservoir for the whole crop.              |
| `position_along_gutter` | integer         | 1 ... 12                                      | Plant position along the gutter, counted from the dosing end (1) to the far end (12).  |
| `head_fresh_mass_g`     | number          | grams, recorded to 0.1 g                      | Fresh mass of the cut head at harvest. This is the response variable.                  |
| `harvest_date`          | date            | `2026-06-15` or `2026-06-16`, ISO YYYY-MM-DD  | Morning on which that gutter was cut. G01-G05 were cut on 15 June, G06-G10 on 16 June. |

There are no missing values in any column.

### Reproducing the file

`make_data.py` writes `lettuce_harvest.csv` using only the Python standard
library and a fixed random seed, so re-running it reproduces the same file:

```
python3 make_data.py
```

### Reproducing the analysis

```
python3 analysis.py
```

The script needs `pandas` and `scipy`, and prints the summary table and the
two-sample test results reported above.
