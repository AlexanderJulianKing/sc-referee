# Nitrate in drinking-water wells: agricultural versus forested catchments

A regional water authority monitored 22 drinking-water wells for six months to ask
whether wells drawing from agricultural catchments carry more nitrate than wells
drawing from forested catchments. Eleven wells sit in agricultural catchments and
eleven in forested catchments. Each well was sampled once a month from January
through June 2025, giving 132 water samples in total.

---

## 1. Data description

The project holds two data files. They describe the same monitoring campaign at two
different levels: one row per water sample, and one row per well.

### File 1: `nitrate_monitoring_log.csv` (raw monitoring log)

**One row represents one water sample: one well measured on one month.**
132 rows plus a header. The six rows that share a `well_id` are repeated
measurements at the same physical well at six successive time points.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `well_id` | text | - | Well identifier, `WEL01` to `WEL22`. Appears on 6 rows, one per sampled month. |
| `catchment_type` | text | - | Catchment the well draws from: `agricultural` or `forested`. Fixed for a well, identical on all six of its rows. |
| `sample_month` | text | - | Month the sample was taken, written `YYYY-MM`, from `2025-01` to `2025-06`. |
| `nitrate_mg_per_l` | number | mg/L | Nitrate concentration measured in that one sample. |
| `water_temp_c` | number | degrees Celsius | Water temperature when the sample was taken. Changes month to month. |
| `well_depth_m` | number | metres | Depth of the well. A fixed property of the well, so it repeats unchanged on all six of that well's rows. |

### File 2: `well_nitrate_summary.csv` (per-well summary)

**One row represents one well, summarising its whole six-month monitoring period.**
22 rows plus a header, one row per well, ordered `WEL01` to `WEL22`.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `well_id` | text | - | Well identifier, `WEL01` to `WEL22`. Unique: each well appears on exactly one row. Matches `well_id` in the raw log. |
| `catchment_type` | text | - | Catchment the well draws from: `agricultural` or `forested`. Agrees with the raw log for the same well. |
| `mean_nitrate_mg_per_l` | number | mg/L | Mean of that well's six monthly `nitrate_mg_per_l` values. |
| `n_samples` | integer | count | How many monthly samples went into that mean. It is 6 for every well. |

### Which file the inference was run on

**The inferential comparison of the two catchment types was run on
`well_nitrate_summary.csv`, the per-well summary file, with one value per well and
22 values in total.** The raw monitoring log was used only to describe the data:
how many wells there are, how many samples each contributed, the monitoring period,
and the spread of the raw measurements.

The reason is the structure of the raw file. The six rows for a well are the same
well measured six times, not six independent wells. Feeding all 132 rows into a
two-sample test would treat repeated looks at one well as if they were separate
wells. That is pseudoreplication, and it inflates the apparent sample size from 22
to 132 while the real number of independent units never changes. The standard error
would come out too small and the p-value too optimistic. Collapsing each well to its
own six-month mean first removes that problem, because the resulting 22 rows are
independent of one another.

---

## 2. Methods

1. **Load both files** with pandas.
2. **Describe the raw log.** Count wells, count samples per well, read off the
   monitoring period, and summarise nitrate, water temperature, and well depth.
   No test is run on this file.
3. **Check the two files against each other.** For every well, recompute the mean of
   its six raw `nitrate_mg_per_l` values and its row count from the raw log, and
   compare them with `mean_nitrate_mg_per_l` and `n_samples` in the summary file.
   Also confirm `well_id` is unique in the summary file and that `catchment_type`
   agrees between the files.
4. **Compare the two catchment types** on `mean_nitrate_mg_per_l` from the summary
   file, using an independent two-sample t-test with Welch's correction for unequal
   variances, two-sided, at alpha = 0.05. Welch's version was chosen because the two
   groups have visibly different spreads (see the standard deviations below), and
   Welch's t-test does not assume they are equal. The sample size is the number of
   wells per catchment type: 11 and 11.
5. **Report an effect size and a confidence interval**, and run a rank-based
   Mann-Whitney U test as a supporting check, since 11 wells per group is a small
   sample and the rank test does not assume the values are normally distributed.

All numbers below were produced by `analysis.py` in this directory, run with Python 3
(pandas 2.0.3, scipy 1.9.1).

---

## 3. Results

### 3.1 Descriptive, from the raw monitoring log

- 132 rows, 22 distinct wells.
- Every well contributed exactly 6 samples (minimum 6, maximum 6).
- Monitoring period: 2025-01 through 2025-06, six monthly rounds.
- 11 agricultural wells (66 rows) and 11 forested wells (66 rows).
- No missing values in any column of either file.

Sample-level nitrate, all 132 measurements, descriptive only:

| catchment_type | samples | mean (mg/L) | SD (mg/L) | min | max |
| --- | --- | --- | --- | --- | --- |
| agricultural | 66 | 7.062 | 1.635 | 3.28 | 10.23 |
| forested | 66 | 2.419 | 1.081 | 0.63 | 5.22 |

Across all samples, water temperature ranged from 8.2 to 15.0 degrees Celsius
(mean 11.32) and well depth from 23.5 to 95.9 metres (mean 55.18).

### 3.2 Consistency between the two files

Every check passed. Both files contain the same 22 wells, `well_id` is unique in the
summary file, `catchment_type` agrees for every well, `n_samples` equals the raw row
count for every well, and each `mean_nitrate_mg_per_l` equals the recomputed mean of
that well's six raw values to within 3.33e-04 mg/L, which is the rounding to three
decimals in the summary file.

### 3.3 The two-group comparison

Run on `well_nitrate_summary.csv`. One value per well, 22 wells.

| catchment_type | wells (n) | mean (mg/L) | SD (mg/L) | min | max |
| --- | --- | --- | --- | --- | --- |
| agricultural | 11 | 7.062 | 1.468 | 4.865 | 9.437 |
| forested | 11 | 2.419 | 0.634 | 1.672 | 3.415 |

Difference in means (agricultural minus forested): **4.643 mg/L**.

Welch two-sample t-test, two-sided:

- t = **9.6303**
- degrees of freedom (Welch) = 13.599
- p = **1.90e-07**
- 95% confidence interval for the difference in means: **3.606 to 5.680 mg/L**
- Cohen's d = 4.106, Hedges' g = 3.950

Supporting rank-based test, Mann-Whitney U: U = 121.0, p = 8.15e-05. This is the
largest U value possible for 11 against 11, meaning every agricultural well had a
higher six-month mean than every forested well.

At alpha = 0.05 the null hypothesis of equal mean nitrate between the two catchment
types is rejected.

Note that the standard deviation of the agricultural group drops from 1.635 at the
sample level to 1.468 at the well level, and the forested group from 1.081 to 0.634.
That gap is the month-to-month noise within a well averaging out. It is also a
reminder that the 132 sample-level numbers carry less independent information than
their count suggests.

---

## 4. Interpretation

Wells in agricultural catchments carried substantially more nitrate than wells in
forested catchments over the six-month period. The average six-month well mean was
7.06 mg/L in agricultural catchments against 2.42 mg/L in forested ones, roughly
three times as much. The best estimate of the gap is 4.64 mg/L, and the data are
consistent with a true gap somewhere between 3.61 and 5.68 mg/L.

The separation is clean rather than marginal. The lowest agricultural well mean
(4.865 mg/L) still sits above the highest forested well mean (3.415 mg/L), so the two
groups do not overlap at all at the well level. The rank test confirms this: it hit
its maximum possible value. The standardised effect size (Hedges' g near 4) is very
large, meaning the gap between the groups is about four times the typical spread
within a group.

Two limits are worth stating plainly.

First, this is an observational comparison, not an experiment. Wells were not
randomly assigned to catchment types. The analysis shows that agricultural
catchments and higher nitrate go together; it does not by itself prove that
agricultural activity caused the nitrate. Well depth and water temperature were
recorded but not used as adjustments in this comparison, and either could differ
systematically between the two catchment types.

Second, the concentration column is named `nitrate_mg_per_l` without stating whether
the value is expressed as the nitrate ion or as nitrate-nitrogen. Those two
conventions differ by a factor of about 4.4, and drinking-water limits are written
against a specific one. Before any of these numbers is compared with a regulatory
threshold, the authority should confirm which convention the laboratory used. This
report deliberately does not compare the results with a numeric limit for that
reason.

### Public-health implication

Nitrate in drinking water matters most for bottle-fed infants, and the wells here are
drinking-water wells, so the difference is not merely academic. The practical
implication for the authority is that catchment land use is a usable screening
signal: wells drawing from agricultural catchments are the ones that warrant
priority monitoring, more frequent sampling, and follow-up at the well head. Two
individual samples in the agricultural group reached 10.23 mg/L (WEL11, 2025-03) and 10.14 mg/L (WEL16, 2025-04), both from
wells whose six-month means were among the highest (WEL11 at 9.437 and WEL16 at
8.387), which suggests that a handful of specific wells, not the agricultural group
as a whole, should be looked at first. Forested-catchment wells, none of which
averaged above 3.42 mg/L, can reasonably sit on a lighter monitoring schedule.
Whether any of these values actually breaches a health standard depends on resolving
the units question above.
