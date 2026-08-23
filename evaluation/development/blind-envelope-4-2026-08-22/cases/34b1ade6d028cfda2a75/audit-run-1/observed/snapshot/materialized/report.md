# Marram grass cover on fenced and unfenced sand dunes

## Question

Does excluding rabbits change the percentage cover of marram grass on mobile sand dunes?

Marram is the grass that builds and holds a mobile dune, and rabbits graze it hard. Ten dunes along
one stretch of coast were surveyed. Five had been fenced against rabbits for three years and five
were left open to them. On each dune, six 1 m quadrats were placed along a fixed line running from
the seaward toe up to the crest, and percentage marram cover was estimated in each quadrat. That
gives 60 quadrat readings of the dune system, and every one of them is used in the comparison
below.

## Data

The analysis reads a single comma separated file, `marram_cover.csv`, with a header row and 60 data
rows.

**A single row is one 1 m quadrat: one percentage cover reading taken at one point along the
transect line.**

| # | Column | Type | Values | Description |
| --- | --- | --- | --- | --- |
| 1 | `dune_name` | text | 10 distinct names | Short name of the surveyed dune the reading comes from |
| 2 | `rabbit_exclusion` | text | `fenced` or `unfenced` | Whether that ground was fenced against rabbits for three years |
| 3 | `quadrat_number` | integer | 1 to 6 | Position along the fixed line, 1 nearest the seaward toe and 6 at the crest |
| 4 | `marram_cover_pct` | integer | 0 to 100 | Estimated percentage cover of marram grass in that quadrat |

Ten dunes were surveyed, six quadrats on each, so 10 x 6 = 60 rows. The fenced ground is Braid
Hollow, Sandhaven, Nether Ness, Salt Pans and Reddings; the unfenced ground is Corrie Links, Kelpie
Bank, Whin Head, Tern Bar and Gull Rigg. There are no missing values, and recorded cover runs from
17 to 67 percent, so nothing sits against the 0 or 100 limit.

## Method

Marram cover was compared between the two treatments with an independent two-sample t-test
(Student's, equal variances assumed), applied to every quadrat row in the table. The test was run
with `scipy.stats.ttest_ind`. All numbers below come from `analysis.py`.

## Results

Cover by treatment, over all quadrat readings:

| Treatment | Quadrats | Mean cover (%) | SD (%) | Median (%) | Range (%) |
| --- | --- | --- | --- | --- | --- |
| `fenced` | 30 | 47.63 | 8.81 | 46.0 | 35 to 67 |
| `unfenced` | 30 | 30.30 | 9.98 | 28.5 | 17 to 63 |

The two-sample comparison:

| Quantity | Value |
| --- | --- |
| Total quadrats surveyed (n) | 60 |
| Mean cover, fenced | 47.63 % |
| Mean cover, unfenced | 30.30 % |
| Difference (fenced minus unfenced) | 17.33 percentage points |
| 95 % confidence interval for the difference | 12.47 to 22.20 percentage points |
| Pooled SD | 9.42 percentage points |
| t statistic | 7.130 |
| Degrees of freedom | 58 |
| p-value | 1.77e-09 (p < 0.001) |
| Cohen's d | 1.84 |

Fenced quadrats carried a mean of 47.63 percent marram cover against 30.30 percent on unfenced
quadrats, a difference of 17.33 percentage points in favour of the fenced ground. With 60 quadrats
in hand the difference is estimated tightly: the 95 percent interval runs from 12.47 to 22.20
percentage points, so even the low end of that range is a substantial gain in cover. The t
statistic of 7.130 on 58 degrees of freedom gives p = 1.77e-09, far below the 0.05 threshold, and
the effect size of 1.84 pooled standard deviations is large.

## Conclusion

Rabbit exclusion increased marram grass cover. Three years behind a rabbit fence left the sward
17.33 percentage points richer in marram than open ground, and the two-sample t-test on all 60
quadrats returns t = 7.130, df = 58, p = 1.77e-09. The result is statistically significant at the
0.05 level, and the size of the gain matters for dune management as well: adding roughly 17 points
of marram cover is the difference between a thinly vegetated face and one with enough tillers to
trap sand and hold the dune together. Fencing is worth the cost where marram cover on a mobile dune
needs to be built up.

## Reproducing

```
/usr/local/bin/python3 analysis.py
```

`analysis.py` reads `marram_cover.csv` and prints every number quoted above. It does not write to
the data file.
