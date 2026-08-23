# Wet versus dry harvesting and marketable cranberry yield

## 1. Summary

Twenty-four production bogs from the cooperative were compared. Twelve were wet-harvested and twelve
were dry-harvested. Wet-harvested bogs averaged 189.76 barrels per acre and dry-harvested bogs averaged
166.97 barrels per acre, a difference of 22.79 barrels per acre in favour of wet harvesting. A Welch
two-sample t-test on the 24 bog-level figures gave t = 2.0652 with 21.32 degrees of freedom and
p = 0.0513. At the usual 0.05 threshold that does not clear the bar, so this study does not establish a
yield difference between the two methods. The 95% confidence interval runs from -0.14 to +45.72 barrels
per acre, so a small loss and a large gain are both still consistent with the data.

## 2. Data description

### The file

One data file, `cranberry_harvest.csv`, at the project root. It has a header row and 24 data rows.

### What one row represents

One row is **one production bog for one harvest season**. Each bog was harvested once, by one method,
and the cooperative wrote down a single marketable yield figure for it. There are no repeated
measurements, no sub-samples taken within a bog, and no split plots.

- The independent unit is the bog.
- There are 24 bogs and 24 rows.
- **Each bog appears exactly once.** All 24 `bog_id` values are distinct, so the number of bogs and the
  number of rows are the same number. The analysis script checks this before it runs any test.

Twelve bogs carry `harvest_method = wet` and twelve carry `harvest_method = dry`. No bog was harvested
both ways, so the two groups are separate sets of bogs rather than two readings from the same bogs.

### The columns

| column | type | units | what it holds |
|---|---|---|---|
| `bog_id` | text | none | Bog identifier, `BOG01` through `BOG24`. Unique across the file, one row per identifier. |
| `harvest_method` | text | none | Method used on that bog. Exactly two values: `wet` (the bog is flooded and floating berries are collected) or `dry` (fruit is picked off the vine with mechanical pickers). |
| `marketable_yield_bbl_per_acre` | number | barrels per acre | Marketable yield recorded for that bog for the season, to one decimal place. This is the outcome of the study. Observed range 128.6 to 246.1. |
| `bog_area_acres` | number | acres | Planted area of the bog, to one decimal place. Observed range 4.2 to 13.3. Yield is already per acre, so this column describes bog size and does not rescale the yield. |
| `cultivar` | text | none | Cranberry variety planted. One of six: `Stevens`, `Ben Lear`, `Early Black`, `Howes`, `Mullica Queen`, `Crimson Queen`. |
| `planting_age_years` | integer | years | Age of the planting at harvest. Observed range 6 to 40. |
| `harvest_date` | date | none | Calendar date the bog was harvested, ISO format `YYYY-MM-DD`, autumn 2025 season. |

The values in this file are invented for this exercise. They are not measurements from real farms. They
were produced by `make_data.py` with a fixed seed, so the file can be regenerated exactly.

## 3. Methods

The question is whether marketable yield differs between the two harvest methods.

Because each bog contributes exactly one row, the rows of the table are the independent units. There is
nothing inside a bog that needs to be averaged first, so a comparison run over the 24 rows is a
comparison over the 24 bogs. That makes an independent two-sample test the correct inferential test
here.

The primary test is **Welch's independent two-sample t-test**, two-sided, on
`marketable_yield_bbl_per_acre` grouped by `harvest_method`. Welch's version does not assume the two
methods have the same spread of yields, which is the safer default when group variances are not known
in advance. The decision threshold is alpha = 0.05.

Before testing, the analysis script confirms the design the test depends on: 24 rows, 24 distinct
`bog_id` values, at most one row per bog, no missing yields, and exactly two method levels with 12 bogs
each. All checks passed.

Three secondary checks are reported for transparency. They are not the basis of the decision, and the
conclusion is taken from the Welch test regardless of how they come out.

The other recorded columns (`bog_area_acres`, `cultivar`, `planting_age_years`, `harvest_date`) are not
used in the comparison. The governing protocol asks for a two-group comparison of yield and did not plan
any adjusted model, so none was fitted.

All numbers below come from running `/usr/local/bin/python3 analysis.py` on the frozen data file.

## 4. Results

### Yield by method

| harvest_method | n bogs | mean (bbl/acre) | SD | min | median | max |
|---|---|---|---|---|---|---|
| dry | 12 | 166.97 | 24.51 | 128.6 | 162.65 | 215.1 |
| wet | 12 | 189.76 | 29.34 | 146.5 | 190.80 | 246.1 |

Sample size is 12 bogs per method, 24 bogs in total.

### Primary test

| quantity | value |
|---|---|
| unit of analysis | one production bog (one row) |
| difference in means (wet minus dry) | 22.79 bbl/acre |
| standard error of the difference | 11.04 |
| t statistic | 2.0652 |
| degrees of freedom (Welch) | 21.32 |
| p-value (two-sided) | 0.0513 |
| 95% confidence interval for the difference | -0.14 to 45.72 bbl/acre |
| Hedges' g | 0.814 |
| decision at alpha = 0.05 | do not reject the null of equal means |

### Secondary checks

| check | statistic | p-value |
|---|---|---|
| Student t-test (equal variance) | t = 2.0652 | 0.0509 |
| Mann-Whitney U (rank-based) | U = 103.0 | 0.0783 |
| Levene test of equal variances | W = 0.7027 | 0.4109 |
| Shapiro-Wilk normality, wet bogs | W = 0.9692 | 0.9018 |
| Shapiro-Wilk normality, dry bogs | W = 0.9805 | 0.9856 |

The Levene and Shapiro-Wilk results give no sign that equal variances or approximate normality are
badly violated. The Student and rank-based tests land on the same side of the 0.05 threshold as the
Welch test, so the conclusion does not hinge on which of the three was chosen.

## 5. Interpretation

Wet-harvested bogs out-yielded dry-harvested bogs by 22.79 barrels per acre on average in this sample,
and the standardised effect size of 0.814 would be a large one if it were real. But the test does not
clear the 0.05 threshold (p = 0.0513), so **this study does not demonstrate that harvest method changes
marketable yield.** The 95% confidence interval stretches from a loss of 0.14 barrels per acre to a gain
of 45.72, which means the data are compatible with anything from no benefit at all to a very large
benefit.

A p-value of 0.0513 should not be read as almost significant or as weak evidence of an effect. It is on
the other side of the line the study set in advance, and with 12 bogs per method the estimate is
imprecise. The width of the confidence interval, roughly 46 barrels per acre from end to end, is the
honest description of what this sample can and cannot tell the cooperative.

Two limits are worth stating plainly.

**The bogs were not randomly assigned.** The cooperative recorded which method each member farm already
used. Bogs that get wet-harvested may differ from dry-harvested bogs in soil, water access, variety, or
management, and any of those could move yield on its own. The comparison shows an association between
method and yield, not a causal effect of switching method.

**Nothing was adjusted for.** Bog area, cultivar, planting age, and harvest date were recorded but not
used. If those differ systematically between the two groups, part of the 22.79 barrel gap could belong
to them rather than to the harvest method.

### Recommendation for growers

Do not change harvest method on the strength of this study. The result is consistent with a real yield
advantage for wet harvesting, but it is also consistent with no advantage, and one season of 24 bogs
cannot separate those two possibilities.

For a grower weighing the decision now, harvest method should be chosen on the grounds this study did
not measure: fruit quality and its effect on price, since dry-harvested fruit is generally sold fresh
while wet-harvested fruit goes to processing; water availability and the cost of flooding; and
equipment and labour costs.

If the cooperative wants a real answer on yield, the next study should be larger and better controlled.
Twelve bogs per method leaves too much uncertainty. Assigning method at random within a farm, or
following the same bogs across seasons under each method, would remove the concern that the two groups
of bogs were different to begin with.

## 6. Files

| file | what it is |
|---|---|
| `cranberry_harvest.csv` | The data. 24 rows, one per bog. |
| `analysis.py` | The analysis script. Run with `/usr/local/bin/python3 analysis.py`. |
| `report.md` | This report. |
| `make_data.py` | The generator that produced the CSV, kept for reproducibility. |
| `DATA_DESCRIPTION.md` | Longer companion description of the data file. |
